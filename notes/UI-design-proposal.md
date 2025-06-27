# UI Design Proposals

This project aims to combine the best aspects of Hebbia and Harvey's UIs, resulting in a familiar and intuitive user experience.

## High-Level Architecture

- **Frontend**:  
  - Built with **React Router** for navigation.
    - https://reactrouter.com/start/framework/installation
    - https://reactrouter.com/start/framework/routing
    - https://reactrouter.com/start/framework/route-module
    - https://reactrouter.com/start/framework/rendering
    - https://reactrouter.com/start/framework/data-loading
    - https://reactrouter.com/start/framework/actions
    - https://reactrouter.com/start/framework/navigating
    - https://reactrouter.com/start/framework/pending-ui
    - https://reactrouter.com/start/framework/testing
    - 
  - Uses **TanStack Table** for advanced table rendering and manipulation.
    - https://tanstack.com/table/latest/docs/introduction
    - https://tanstack.com/table/latest/docs/overview
    - https://tanstack.com/table/latest/docs/installation
    - https://tanstack.com/table/latest/docs/framework/react/react-table
    - https://tanstack.com/table/latest/docs/guide/data
    - https://tanstack.com/table/latest/docs/guide/column-defs
    - https://tanstack.com/table/latest/docs/guide/tables
    - https://tanstack.com/table/latest/docs/guide/row-models
    - https://tanstack.com/table/latest/docs/guide/rows
    - https://tanstack.com/table/latest/docs/guide/cells
    - https://tanstack.com/table/latest/docs/guide/header-groups
    - https://tanstack.com/table/latest/docs/guide/headers
    - https://tanstack.com/table/latest/docs/guide/columns
    - https://tanstack.com/table/latest/docs/framework/react/guide/table-state

  - Shadcn with tailwind
    
  - Written in **TypeScript** for type safety.
  - Communicates with a backend via a file-based API.

- **Backend**:  
  - Implemented in **Python** using **FastAPI**.
  - Structured as three separate services, following FastAPI best practices for modularity and maintainability.

## UI Description
- https://21st.dev/originui/table/data-table-with-filters-made-with-tan-stack-table

- **Initial State**:  
  - The UI starts as a blank table with no columns (controls) or rows (uploaded files).
  - Columns represent controls, each with a title and description (e.g., questions to be answered for each document).
  - Rows represent uploaded files.

- **Document Display**:  
  - The first column displays the document file itself.
  - Each file is shown as a badge or button component, displaying the file name.
  - Clicking the badge/button links to the signed URL for the file, allowing users to access the document directly.

- **Adding Data**:  
  - Users can add new rows by uploading documents.
  - When clicking "Add Row(s)", a modal appears, allowing users to upload one or more documents.
  - The number of rows added corresponds to the number of documents uploaded in the modal.

- **Adding Controls/Questions**:  
  - Users can append new questions (with titles) as columns to the existing table.
  - This allows for dynamic expansion of the table as new controls/questions are needed.

## Visual Reference

- Refer to the second screenshot for an example layout:
  - The first column contains the document file (as a badge/button).
  - Additional columns represent questions/controls.
  - The table grows dynamically as users add files (rows) and questions (columns).

## Summary

This design provides a flexible, extensible tabular interface for managing documents and associated questions, leveraging modern React and FastAPI best practices for a robust and maintainable application.
