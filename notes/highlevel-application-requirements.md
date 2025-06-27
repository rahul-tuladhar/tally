# Application Requirements

## Tabular View

- All fields, values, and descriptions are **editable**.
- Ability to **delete rows/columns**:
  - Deleting a row/column should also delete the associated file in the storage bucket and remove it from the database.
- For most language models, the entire document can be included in the context of the call (at the cost of more tokens), which is acceptable for a proof of concept.
- **Async calls** per document are sent out to OpenAI.
  - Need to consider rate and token limits for async/batch processing, especially when handling 10+ documents.

## Document Upload

- Support for uploading documents (single or batch).
- Persist uploaded documents in a storage bucket or similar, using signed URLs.
- This functionality could be implemented as a small, contained service that wraps external calls to the bucket provider.

## Tabular View Features

- Easy way to:
  - **Add Column/Control**: Each column should have a title and a question that needs to be answered for each document in that column.
  - **Add Row/Document**.

## Document Parsing

- Parse uploaded documents to extract structured data (likely using the Reducto API).
- Optionally persist the structured data for future reuse in OpenAI calls.
- This could be implemented as an internal service that wraps an external Reducto client to interface with their API.
