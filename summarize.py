import os
from dotenv import load_dotenv
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

prompt_template = """Your job is to write a brief, concise summary, at most 100 symbols, of the following email message.
The email's subject appears in the first line.
Provide an email priority as a rank from 1 to 5, where 1 is an important, urgent message required immediate response, and 5 is a spam. 
Generate a brief response to the given email. 
Return a result in the format:

SUMMARY=summary
PRIORITY=priority
RESPONSE=response

"{text}"
CONCISE SUMMARY:"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

SENDER = "SENDER"
PRIORITY = "PRIORITY"
SUMMARY = "SUMMARY"
RESPONSE = "RESPONSE"


def summarize(subject, text, open_api_key):
    """Summarize given subject and text, returns dictionary with the
        PRIORITY, SUMMARY, and RESPONSE keys
    """

    full_text = f"Subject: {subject}\n\n{text}"
    docs = [Document(page_content=full_text)]
    llm = OpenAI(temperature=0, openai_api_key=open_api_key)
    summary_chain = load_summarize_chain(llm, chain_type="refine", question_prompt=PROMPT)
    raw_summary = summary_chain.run(docs)

    res = {}
    raw_fields = raw_summary.split("\n")
    for field in raw_fields:
        parts = field.split("=")
        if len(parts) == 1:
            res["SUMMARY"] = parts[0].strip()
        else:
            res[parts[0]] = parts[1].strip()
    return res


summarize_res_by_message_id = {}
postponed_messages_ids = []  # low priority message IDs


openai_api_key = os.getenv("OPENAI_API_KEY")


def process_message(gmail_message_id, sender, subject, text):
    """Entry point, Gmail hook calls it"""
    # Getting priority, summery and response for email
    summarize_res = summarize(subject, text, openai_api_key)
    summarize_res[SENDER] = sender

    # Saving results from email handler
    summarize_res_by_message_id[gmail_message_id] = summarize_res


    priority = int(summarize_res[PRIORITY])
    summary = summarize_res[SUMMARY]
    response = summarize_res[RESPONSE]
    print(summarize_res)
    # Sending notification to messenger for email with height priority (1 or 2)
    if priority < 3:
        action_list = [
            {"type": IGNORE_MAIL},
            {"type": OPEN_MAIL, "id": gmail_message_id},
            {"type": REPLY_MAIL, "id": gmail_message_id, "response": response}
        ]

        text = f"Ви отримали важливий email від {sender}:\n{summary}"
        # Sending to messenger
        format_message("", text, action_list)
    else:
        postponed_messages_ids.append(postponed_messages_ids)


def respond_rest():
    """ IN PROGRESS...
    Handler for low priority emails
    """
    digest = ""
    for gmail_message_id in postponed_messages_ids:
        summarize_res = summarize_res_by_message_id[gmail_message_id]
        sender = summarize_res[SENDER]
        summary = summarize_res[SUMMARY]

        digest += f"Від: {sender}: {summary}\n"
        summarize_res_by_message_id.pop(gmail_message_id)

    format_message("", digest, [])
    postponed_messages_ids.clear()


# Function sends notification to messenger
def format_message(chat_id, text, action_list):
    # TODO messenger callback
    pass


IGNORE_MAIL = 0
OPEN_MAIL = 1
REPLY_MAIL = 2


def react(gmail_message_id, reaction):
    """
    The function receives a response from the messenger and calls the corresponding function
    """
    if reaction == IGNORE_MAIL:
        pass

    elif reaction == OPEN_MAIL:
        # open gmail message with gmail_message_id using GMail Toolkit
        open_gmail_message(gmail_message_id)

    elif reaction == REPLY_MAIL:
        # generate draft of the reply to gmail message with gmail_message_id using GMail Toolkit
        summarize_res = summarize_res_by_message_id[gmail_message_id]
        reply_gmail_message(gmail_message_id, summarize_res[RESPONSE])

    summarize_res_by_message_id.pop(gmail_message_id)


def open_gmail_message(gmail_message_id):
    # TODO gmail callback
    pass


def reply_gmail_message(gmail_message_id, response):
    # TODO gmail callback
    pass


def main():
    """Function for module testing"""
    subject = "Urgent: Critical Issues Identified in Current Project - Immediate Requirement Changes & Meeting Request ASAP"
    text = """
    Dear Mr. Smith,

I hope this email finds you well. I am writing to urgently address some critical concerns that have emerged during the course of our current project.
 
It has come to our attention that certain aspects of the project plan and requirements need immediate attention and modification.

Upon thorough analysis and feedback from stakeholders, we have identified several key areas where the current project falls short of meeting the desired objectives. 

These issues include [list specific problems or shortcomings].

To ensure the project's success and alignment with our goals, it is imperative that we make prompt requirement changes to address these concerns. 

I kindly request your immediate attention and collaboration in addressing the following actions:

1. Conduct an urgent review of the identified problem areas and their impact on the project's overall success.

2. Form a dedicated team to thoroughly assess the current requirements and propose necessary modifications.

3. Prioritize the implementation of required changes to mitigate risks and improve project outcomes.

4. Communicate the need for immediate requirement changes to all relevant stakeholders, emphasizing the importance and urgency of their involvement.

I urge you to treat this matter with the utmost urgency. We need to act swiftly to prevent any further setbacks and ensure the project's timely delivery within the defined parameters.

I am counting on your expertise and support in leading the effort to address these issues promptly. Should you require any additional resources or assistance, 

please do not hesitate to reach out to me or the designated project team.

Let's work together to overcome these challenges and steer the project towards success. Thank you for your immediate attention and cooperation.

Best regards,

John Watson.
    """

    res = summarize(subject, text, openai_api_key)
    print(res)

    print(res[PRIORITY])
    print(res[SUMMARY])
    print(res[RESPONSE])


if __name__ == "__main__":
    main()
