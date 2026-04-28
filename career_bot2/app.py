import os
import json
import requests
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]



class CareerBot:

    def __init__(self):
        load_dotenv(override=True)
        self.openai = OpenAI()
        self.linkedin = ""
        self.resume = ""
        self.name = "Aniruddh Khera"
        for page in PdfReader("./assets/Profile.pdf").pages:
            text = page.extract_text()
            self.linkedin += text
        for page in PdfReader("./assets/Aniruddh resume.pdf").pages:
            text = page.extract_text()
            self.resume += text
    

    
    def record_user_details(self, email, name="Not provided", notes="Not provided"):
        msg = f"Recording user details: email:{email}, name:{name}, notes:{notes}"
        self.push(msg)
        return {"status": "ok"}


    def record_unknown_question(self, question):
        msg = f"Recording unanswered question: {question}"
        self.push(msg)
        return {"status": "ok"}



    def push(self, msg):
        push_over_user = os.getenv("PUSH_OVER_USER")
        push_over_app_token = os.getenv("PUSH_OVER_APP_TOKEN")
        push_over_url = "https://api.pushover.net/1/messages.json"
        response = requests.post(
            push_over_url,
            data={
                "user": push_over_user,
                "token": push_over_app_token,
                "message": msg,
            }
        )
        print(response.content)

    def system_prompt(self):
       
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Resume:\n{self.resume}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, msg, history):
        messages = [{"role": "system", "content": self.system_prompt()}]
        for user_msg, assistant_msg in history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": msg})

        completed = False
        while not completed:
            resp = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
            finish_reason = resp.choices[0].finish_reason
            if finish_reason == "tool_calls":
                tool_calls = resp.choices[0].message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(resp.choices[0].message)
                messages.extend(results)
            else:
                completed = True
        return resp.choices[0].message.content

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            print(f"tool called {tool_call.function.name}")
            arguments = json.loads(tool_call.function.arguments)
            tool_fn = getattr(self, tool_call.function.name, None)
            res = tool_fn(**arguments) if tool_fn else {"error": "tool not found"}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(res),
                    "tool_call_id": tool_call.id,
                }
            )
        return results




if __name__ == "__main__":
    bot = CareerBot()
    gr.ChatInterface(bot.chat).launch(server_name="0.0.0.0", server_port=7860)
