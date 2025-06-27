Project Structure
This is very similar to what we are doing. The functional way of splitting things doesn’t really work except for really small projects, so we also have a “module” based approach. Our application looks something like:

ourproject-backend
├── alembic/
├── app
│   ├── auth
│   │   ├── routes.py
│   │   ├── schemas.py  # pydantic models
│   │   ├── models.py  # db models
│   │   ├── permissions.py # our decorator
│   │   ├── exceptions.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── core
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── ....
│   ├── users
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── ....
│   ├── tenants
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── ....
│   ├── extensions
│   │   ├── logs.py # JSON Logger etc
│   │   ├── middleware.py # correlation ID & request tracker
│   │   ├── ....
│   ├── services
│   │   ├── mailer.py # a client to SES
│   │   ├── filesystem.py #  a wrapper over S3
│   │   ├── ....
│   ├── db
│   │   ├── mixin.py
│   │   ├── base.py
│   │   ├── engine.py
│   │   ├── ....
│   ├── utils
│   │   ├── schemas.py
│   │   ├── helpers.py
│   │   ├── ....
│   ├── modules
│   │   ├── module_a
│   │   │   ├── models.py
│   │   │   ├── routes.py
│   │   │   ├── schemas.py
│   │   │   ├── ....
│   │   ├── module_b
│   │   │   ├── models.py
│   │   │   ├── routes.py
│   │   │   ├── schemas.py
│   │   │   ├── ....
│   ├── config.py # where the Dynaconf singleton lives
│   ├── exceptions.py
│   ├── routes.py # registration of all system routes
│   ├── hub.py # our event hub
│   └── main.py
├── tests/
│   ├── users
│   ├── tenants
│   └── module_a
├── .env
├── .secrets.toml
├── .gitignore
├── settings.toml
├── mypy.ini
└── alembic.ini
A few comments:

We use a sort of “mixed” structure in the sense that some global/generic modules (like Users/Tenants/Auth) have all the same structure and are in the top level, but the application specific business logic is in the modules module. We have been using this structure for the past couple of years and have been pretty happy with the separation of concerns it brings. We even reuse the same blueprint for different projects, we mostly just change the modules which is great.
Having a specific db module on the top level has helped a lot giving us flexibility to have more robust Mixin classes, better engine configuration and some other goodies.
We also are really happy with having a core module on the top level. This gives us flexibility to do things like a specific mock service, a taskStatus route or more generic resources.
We really like how predictable this is and much boilerplate code we can just copy around from module to module. We have dramatically speed up our development process of new modules with this. This also helped a lot new devs to understand the codebase logic.
Permissions & Auth
Although the “recommended” way of doing authentication in FastAPI would be the dependency injection, we have chosen to use a class-based decorator to control access on the route level.
So our routes look something like:

@route.get('/me')
@access_control(Resources.users_view_self) # this is a enum
def myroute(self):
...

@route.get('/superuser_only')
@access_control(superuser=True)
def myroute(self):
...


@route.get('/open')
@access_control(open=True)
def myroute(self):
...
And our access_control class looks like:

class access_control:  # pylint: disable=invalid-name
    MASTER_USER_ID = 0

    def __init__(
        cls,
        module: Optional[AppModules] = None,
        resource: Optional[AppActions] = None,
        superuser: bool = False,
        open: bool = False,
    ) -> None:
        cls.module = module
        cls.resource = resource
        cls.superuser = superuser
        cls.open: bool = open
        cls.tenant_id: Optional[int] = None
        cls.object_id: Optional[int] = None
        cls.current_user: Optional[UserResponse] = None
        cls.request: Optional[Request] = None
        cls.headers: Optional[dict[Any, Any]] = None
        cls.auth_header: Optional[str] = None
        cls.token: Optional[str] = None

    def __call__(cls, function) -> Callable[..., Any]:
        @functools.wraps(function)
        async def decorated(*args, **kwargs):
            t0 = time.time()
            try:
                await cls.parse_request(**kwargs)
                is_allowed = await cls.verify_request(*args, **kwargs)
                if not is_allowed:
                    raise HTTPException(403, "Not allowed.")
                return await function(*args, **kwargs)
            except exc.NotAllowed as error:
                raise HTTPException(403, str(error)) from error

        return decorated

    async def parse_request(cls, **kwargs) -> None:
        """Get the current user from the request"""
        dependencies = kwargs.get("self", kwargs.get("base_args"))
        base_args: Optional[RequestArgs] = getattr(dependencies, "base_args", None)
        if not base_args:
            return
        cls.tenant_id = base_args.tenant_id
        cls.current_user = base_args.current_user
        return None

    async def verify_request(cls, **kwargs) -> None:
        """Actually check for permission based on route, user, tenant etc"""
        ...
A few benefits we encountered, and few drawbacks:

This is great to accept multiple parameters like module or action or superuser=True and things like that.
The permission controller (the access_control class itself) is fairly easy to work on, being very powerful at the same time, since it has the *args and **kwargs from the request, and the full context (current user, path, tenant, etc), so all sort of checks can be used. As we increase the granularity over access control we have been considering implementing a permissions decorator for each module, so we can have more specific control over a given resource. But WIP still.
Class-based Services
Our service module service.py started to get big and a mess of functions, so we started having a few class based services, which have been working very well. Something like TenantService , UserService. This almost looks like a repository for simple modules (in some cases we even spiltd the service into service and repository (for more complex business logic). Now each service module has anything from 1 to 10 service classes, this greatly improved our organization and readability.

Class-based views
Earlier this year we refactor all of our routes to use a class based view that is included in the fastapi-utils package and this is made our code a lot cleaner. The main benefit for us, is that the basic authentication process (reading the token and the X-Tenant-ID for the header) is done in one place only, se we don’t have to repeat the dependencies.
What we’ve done is, we have a custom commons_deps function, and at the beginning of each route class we do something like:

@cbv(router)
class MyModuleRouter:
    commons = Depends(commons_deps)
    service = MyModuleService()		

    @route.get('/me')
    @access_control(Resources.users_view_self)
    def myroute(self):
         # And now here we can access the common deps & the service
         current_user = self.commons.current_user
         tenant_id = self.commons.tenant_id
         response = self.service.get_module_resource(tenant_id)
We have been experimenting with something slightly different nowadays, which is having the service being instantiated with the tenant_id and current_user in a dependency injection, so that our service starts up a bit more complete.

Task Queues
We are long time Celery users, but celery is overwhelming and fairly difficult to reason about when you get to the internals and specifics. We just switched to RQ and couldn’t be happier with a few caveats. The logic is amazing (the Queue , Job objets are really intuitive and easy to work with, as are dependency chains with depends_on. The thing is that there’s an issue with async functions. They work if you use the worker, but won’t work if you run in the same process, which is kind of a pain when debugging. We haven’t experimented with starlette’s. Background jobs as we always valued having a centralized dashboard for tasks and an easy way to get a task status for example. As we deploy most of our applications in Kubernetes, being able to scale the workers easily and indefinitely is awesome and we are really glad with it. I have been experimenting with a few different snippets to try to open a PR and make RQ compatible in every scenario.

The fancy architecture
In same cases (actually projects) we slightly changed our module architecture to account for a proper business oriented Model object.

...
│   ├── modules
│   │   ├── module_a
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   ├── orm.py # the sqlalchemy classes
│   │   │   ├── models.py # "pure" modules (are also pydantic)
│   │   │   ├── schemas.py # the pydantic API schemas
│   │   │   ├── adapters.py
│   │   │   ├── builders.py
│   │   │   ├── interfaces.py
│   │   │   ├── repository.py
For fancier implementations this worked very well, although is a lot more complex to start with. This gives us a proper EntityModel and great separation of concerns, but it gets a lot more verbose really quick, so we found it was only worth it for very complex projects, but it’s also a possibility.

Custom Response Serializers & BaseSchema
We found that the response_class in FastAPI also serializes the data in Pydantic, so it’s not purely for documentation. You can, however, overwrite the default response behavior by making a custom response class, which we did going a bit of performance (anywhere from 50-100ms) and flexibility. So we have something like:

# utils/schemas.py

class JSONResponse(Response):
    media_type = "application/json"

    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: t.Optional[t.Mapping[str, str]] = None,
        media_type: t.Optional[str] = None,
        background: t.Optional[BackgroundTasks] = None,
    ) -> None:
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.background = background
        self.body = self.render(content)
        self.init_headers(headers)

    def render(self, content: BaseSchema | list[BaseSchema] | Any):
       # This is not 100% battle proof, but as our services are controlled (only return Pydantic modules) works fine
        if isinstance(content, BaseSchema):
            return content.json().encode("utf-8")
        if isinstance(content, list):
            if isinstance(content[0], BaseSchema):
                def uuid_decoder(obj):
                    if isinstance(obj, UUID):
                        return str(obj)
                return orjson.dumps([item.dict() for item in content], default=uuid_decoder)
And then we use the response directly like:

@cbv(router)
class MyModuleRouter:
    commons = Depends(commons_deps)
    service = MyModuleService()		

    @route.get('/me', response_class=[...])
    @access_control(Users.view_self) # this is a enum
    def myroute(self):
        # And now here we can access the commons
      	current_user = self.commons.current_user
      	tenant_id = self.commons.tenant_id
        response = self.service.get_module_resource(tenant_id)
	return JSONResponse(response, 200)
This gave us a cleaner router since we can use the status code on the response itself, which was more intuitive for use, gained a bit of performance with the orjson encoder and we just like it better. The (big) downside is that we face the risk of having documentation/API inconsistencies, in our case it happened once or twice, but we think it’s still worth it.

Just as you guys we also have a BaseSchema base for all Pydantic schemas we use that have a couple of configurations like orm_mode enum etc.

Using a DefaultResponse class
In several occasions the response is kind of generic, so we use a lot of a schema called DefaultResponse:

class DefaultResponse(BaseSchema):
    status: bool
    msg: str
    details: Optional[dict[Any, Any]] = {}
This is a kind of standardized way of communicating with our client (we have a React frontend) so the front devs always know what to look for when getting a DefaultResponse.

Configuration
Although Pydantic is nice for configuration as well, we couldn’t be happier using the amazing @dynaconf lib, developed and maintained by @BrunoRocha. This was a game changer in our settings management.

All of our settings/secrets went to .toml files and a few things happened:
- Only one file for multiple environments using toml headers
- Only one place to manage keys (in Flask we were used of having multiple configuration classes which were a pain to maintain)
- a singleton with global access our settings.py file has ~10 lines:

#app/config.py

from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=[".settings.toml", ".secrets.toml"],
    envvar_prefix="MYAPP",
    env_switcher="MYAPP_APP_ENV",
    load_dotenv=True,
    environments=True,
)
And now everywhere we can just

from app.config import settings

myvar = settings['MYVAR']
myvar_a = settings.MYVAR_A
And don’t need to change anything when deploying to K8S since we already inject everything with env vars (config). Can’t recommend it more. We still have to experiment with the Vault integration, which is the next step.

The Message Hub
This helped a lot while we were trying to further decouple our services.
The hub is a centralized hub to share message between modules, something like:

class MessageHub:
    """Message hub for events"""

    handlers = {
        module_a.ResourceCreated: [
            module_b.handle_resource_created,
            module_c.handle_resource_created,
        ],
        module_d.ResourceDeleted: [
            module_b.handle_resource_deleted,
            module_c.handle_resource_deleted,
        ],
    }  # type: dict[Type["Event"], list[Callable[..., Any]]]

    @classmethod
    async def track(cls, event: ApplicationEvent):
        """Tracks the Application activity.
        Receives the application event that will be used by the AuditService.

        Args:
            event (ApplicationEvent): The ApplicationEvent
        """
        await AuditService.save(event)

    @classmethod
    async def handle(cls, event: Event):
        """
        Handles an arbitrary event.
        It will receive the event, and get the handlers that should handle
        the event. The order on which the handlers will execute the event may vary.
        If the event is sent to the worker, the handlers are async, meaning they can run at the same time.
        If the event is synchronous, than each handlers will handle the event sequentially.

        Args:
            event (Event): The Event.
        """
        if type(event) not in cls.handlers:
            logger.info("No handlers for event: %s", event.__class__.__name__)
            return

        # Call listeners functions
        for fn in cls.handlers[type(event)]:
            if event.is_async:
                worker.enqueue(fn, event)
                return

            await fn(event)
And in most modules we have handlers.py module that will have a few functions that handle events. The services themselves usually dispatch events, like hub.MessageHub.handle(event_created_by_the_service), and we also use it to track application activity, normally called by the route hub.MessageHub.track(application_activity_schema)

Types & Docs
100% of arguments are typed and 100% of methods / functions have docstrings. I honestly can't live without anymore. Now wondering if could just compile the whole code to C and make it fly? Nuitka, MyPyC maybe? TBC...

Now the bad part, and our (really) bad practices

Local Session Management
For a couple of reasons we didn’t implement the request-coupled session management (inject the session through FastAPI’s dependency injection system) and we ended up having a lot of services that handle the session locally, which is not cool and not recommended by SQLAlchemy. Think of:

class ModuleService:
    ...
    async def module_method(self, ...):
       # Terrible
        async with async_session() as session:
	    ...
	return something
Managing the session lifecycle itself is fairly ok and it works for really simple services, but what we found is that for more complex services methods that call on another you end up nesting sessions which is terrible. Imagine calling other_method from module_method that also has the same session lifecycle management, now you just opened a session within another session. Jus terrible. We are gradually moving to better session management, but we are still trying to find better ways of handling it.

Little use of the Dependency Injection
In your write up a lot of great example of how to properly use and leverage the power of dependency injection, we don’t use much of those, and we definitely should.

Lack of Context in Services
Sometimes we found ourselves having a Service class that didn’t even have a initializer and was purely for organization, this is fine, but we are missing a lot of benefits of having some context in the service (example: tenant_id and session) which would save was from having the tenant_id being passed to every single method in a service class. So there’s definitely a lot to improve here.

There's obviously a lot to improve and a whole lot more of bad things that I probably forgot to mention, but again, I though it was worth sharing the experience. And to finish our Dockerfile, which is also pretty simple (using poetry and leveraging it's dev-dependencies logic something that was mentioned here as well #1 :

FROM python:3.10-slim
WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock* .

RUN apt-get update -y && \
    apt-get install gcc -y && \
    apt-get install libpq-dev -y && \
    python -m venv .venv && \
    .venv/bin/pip install poetry && \
    .venv/bin/poetry export -f requirements.txt --output requirements.txt --no-dev --without-hashes && \
    .venv/bin/pip install -r requirements.txt && \
    apt-get remove gcc -y && \
    apt autoremove -y

ADD . /app
EXPOSE 8000
CMD [".venv/bin/uvicorn", "app.asgi:app", "--host", "0.0.0.0"]