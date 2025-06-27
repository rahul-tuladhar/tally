Tabular Review

In a likely scenario in Tally, an auditor may want to get some information from across multiple documents, whether specific questions (“What is the policy effective date?”) and/or inference-style questions (“What are potential risks with this policy?”). These are typically specific to a control, e.g., “Company has established an appropriate governance structure.”). An auditor will review documents, other inputs and requests for information, etc, to determine whether the test of the control is successful and there are no exceptions (passing score).

You’ll make use of:

* OpenAI for prompts and responses: a key will be provided  
  * Key: sk-proj-K3aMXkU2XS8TBzb2yuN\_TkTD43rRnR\_sdpUlJBffuM6IFTy82\_IM52k9nK7\_HXoAchjWEUB8oxT3BlbkFJ0cb0uuP-Zk5GToIIJHe6tzGMbOEF2R-ZaifG9h5LcvNXZQbZD-PXNZ6RsLrztELAn9GyoBbbIA  
* Reducto for computer vision/vision-based models: a key will be provided  
  * Key: fc93b771a0beb0a3deeec3d9c73b7245d58a7986b3c99230fe3c5b661838d3e3594d69ae3bbab8d2e1bcabf80a538b5d   
  * [Reducto documentation](https://docs.reducto.ai/overview) and [/extract documentation](https://docs.reducto.ai/extraction/extract-overview), [reference](https://docs.reducto.ai/api-reference/extract).  
  * Read about the Reducto schema required in each API request.  
* For uploading docs to storage, a Supabase DB \+ storage bucket is simplest, and you can pass the document URL to Reducto in the /extract endpoint.

Allow an auditor to input a control name and description, creating a control.

Within the control, allow an auditor to upload 1 or more documents they would like to search or ask across. Build this is a tabular review UI. This is commonly used by AI workflow startups like Harvey (see [here](https://www.vecflow.ai/blog/introducing-tabular-review)) and [Hebbia](https://hebbia.co/). (Feel free to design this the way you want). 

An auditor should be able to see all the uploaded documents on the left side, and add more documents. The auditor should also be able to add columns, name the column, and add a prompt to the column (e.g., “What is the policy effective date?”). The auditor can add multiple columns. 

Once a relationship exists between a row and column (document and column with valid prompt and name), it should start spinning in the cell to indicate the app is looking for the answer. Here is where you’d make a Reducto call, to extract data, and pass through the data and the prompt (plus any other column details and details about the control) to OpenAI to get a response and make it immediately available in the cell for the auditor to review. 

Time allotting:

* Allow an auditor to regenerate cell responses.  
* If an auditor updates a column (e.g., prompt), regenerate all the relevant column cells.   
* Clicking into a cell, preview the PDF/document and the highlighted citation (Reducto provides citations in their API response if requested in the API call).

Notes

- Debrief at like 4:30pm  
- Collaboration is necessary  
- Likely product in tally, an auditor can have questions about documents  
- This company needs correct governance structure, charter documents, etc. Lots of controls.  
- They don’t hvae the time to view all docuemnts  
- Within control area, upload documents, ask specific questions, what is the effective signing date of the policy, AI needs to look for in the document, comparison of question between control, governance control, this specific documents  
- What is a control?  
  - This company governance mechanism  
  - Rule or requirements for an auditor wants to have  
- They want to ask quetsions about risks  
- E.g. risk idea is to do this in a   
- Tabular review, documents on the left and columns each of the row is document  
- Ideally the moment there is a relationship between document   
- Tally 17 policy questions example documents  
- Upload documents into a storage bucket, store the data in some sort of db write calls to openai and reducto,  
- Explain how you built and walk through in 10 minutes

Initial Questions

- Are there limits to the size of the documents?  
  - Policy documents, largest is company handbook is 9 pages, 110kb,   
- How many documents should we be able to handle within one tabular review view?  
  - Should be able to add as many in the view, as long as you get up to 17 documents   
- Doesn’t matter about the amount of controls with table views  
- Should we focus on correctness or speed? Whats a reasonable amount of time to spend for API calls  
  - No eval, but speed in seconds, moment response is available from API

  Requirements

- Tabular view  
  - All fields, values, and descriptions are editable  
  - Ideally we would be able to  “delete” the row/column \-\> just delete associated file in storage bucket/file, delete from our database as well  
  - With most language models, we can just stuff the entire document in the context of the call, at the cost of more tokens, but it’s probably easier for poc.  
  - Async calls per document sent out to openai, probably have to think about rate/token limits here for async/batch as there might be 10+ documents.  
- Upload documents, single/batch  
  - Persist document in a bucket or similar in signed url  
  - This could be its own small contained service with wrapped external call to the bucket provider  
  - Within the tabular view, we need to have easy way to   
    - “Add Column/Contorl”: this means have a title for that column, and the question that needs to be answered per document within the column  
    - “Add Row/Document”  
- Parse the uploaded documents  
  - Gets structured data, this would likey be the reducto api call here  
  - Could persist this as well to save it for future reuse on openai call  
  - This would be its’ own internal service with wrapped external reducto client to interface to their API  
- UI Design Proposals, a mix between hebbia and harvey  
  - High level architecture based on familiarity  
    - React router, tanstack table, in typescript with file based api backend  
    - Python fast api backend with the 3 separate services, based on fastapi best practices  
- ![][image1]  
- ![][image2]  
- Ideally i like the second one, but hopefully can have something like both.  
- Describing the UI:  
  - A blank UI would just be a table without columns (controls as title and description ) or rows (uploaded file).   
  - Look at the second screenshot and see how in the first column we have the document file itself. This can just be shown as the badge or button component with the name of the file, that we could link to the signed url of the file itself.  
  - We would allow the user to have a modal that appears when they click add row(s) based on the number of documents that are uploaded in that modal, and we also way to append questinos with their titles as columns to the existing table.  