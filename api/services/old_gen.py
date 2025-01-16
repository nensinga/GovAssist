def generate_response_old(request: dict) -> str:
    """
    Generates a response based on the user's request and interaction.
    Supports all government ministries.
    """
    print("Starting to generate response.")

    # Step 1: Extract ministry_id from the request (default to 'general')
    ministry_id = request.get("ministry_id", "general")  
    logger.debug(f"Ministry ID set to: {ministry_id}")

    base_messages = [
        {
            "role": "system",
            "content": "You are a friendly and helpful assistant with expertise in various government services. "
                       "I can help with DMV, Health, Education, and Tax-related queries. "
                       "My goal is to simplify processes and make things clear with a little bit of humor along the way."
        }
    ]
    
    # Step 2: Append user's query to the message
    base_messages.append({"role": "user", "content": request['question']})
    logger.debug(f"User question added to message: {request['question']}")

    try:
        # Step 3: Detect the ministry based on the query
        logger.debug("Detecting ministry based on user query.")
        ministry_response = detect_ministry(request['question'])
        ministry_id = ministry_response.get("ministry", "general")  # Default to "general" if not found
        logger.debug(f"Detected ministry: {ministry_id}")

        # Step 4: Modify the system message based on the detected ministry
        if ministry_id == "dmv":
            base_messages[0]["content"] += " I specialize in DMV services like driver's license and vehicle registration."
        elif ministry_id == "health":
            base_messages[0]["content"] += " I can assist with health-related services, including applications and insurance."
        elif ministry_id == "education":
            base_messages[0]["content"] += " I can guide you through educational services like scholarships and student loans."
        elif ministry_id == "tax":
            base_messages[0]["content"] += " I can help you with tax filing, refunds, and other financial matters."
        else:
            base_messages[0]["content"] += " I can help with general government services."

        # Step 5: Initial API call to generate the response using function calls for documents
        logger.debug("Making API call to OpenAI to generate response.")
        response = client.chat.completions.create(
            model=CHAT_MODEL_NAME,
            messages=base_messages,
            functions=tools_definition  # Pass tools_definition for function calls
        )
        logger.debug(f"Received API response: {response}")

        # Step 6: Extract the first response from the chat model
        initial_message = response.choices[0].message
        logger.debug(f"Initial message content from API: {initial_message.content}")

        # Step 7: Check if documents are needed based on the user's request
        requires_document = any(keyword in request['question'].lower() for keyword in ["form", "document", "application", "download"])
        logger.debug(f"Does the user require documents? {'Yes' if requires_document else 'No'}")

        # Step 8: If documents are needed, call the get_documents_links function
        if requires_document:
            logger.debug(f"Retrieving documents for ministry '{ministry_id}' based on user query.")
            documents_response = get_documents_links(ministry_id, request['question'])
            document_links_html = ""
            if documents_response['documents']:
                for doc_info in documents_response['documents']:
                    document_links_html += f'<p><a href="{doc_info["url"]}" download="{doc_info["document_name"]}">{doc_info["document_name"]}</a></p>'
                grok_response = (
                    f"It seems like you need some official documents. Here are the relevant documents: "
                    f"{document_links_html} Let me know if you need help filling them out!"
                )
                logger.debug(f"Generated document links: {document_links_html}")
            else:
                grok_response = "I couldn't find any documents based on your request. Could you please be more specific about the document you need?"
                logger.debug("No documents found based on user query.")
        else:
            grok_response = f"Great question! Here's what I found: {initial_message.content}"
            logger.debug(f"Generated response without documents: {grok_response}")

        # Step 9: Return the final response including document links if applicable
        logger.debug(f"Final response to return: {grok_response}")
        return grok_response

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")
