from openai import OpenAI
from flask import jsonify, request
from tools.toolbox import HelperTools
from dotenv import load_dotenv
import os
import json
from services.recipeService import recipePromptGeneration
tools=HelperTools()
load_dotenv()
request_keys = ['ingredients', 'allergies']
prompt_request = """Suggest {0} {1} with ingredients including {2}; 
                 considering that I'm allergic to {3}. Provide the results only in Json format."""
client = OpenAI(
  api_key=os.getenv("OPENAI_APIKEY_RECIPE")
)

def createRecipePrompt():
    data = request.get_json()
    prompt=recipePromptGeneration(data)
    return prompt, 200

def generateRecipe(model="gpt-3.5-turbo-1106"):
    data = request.get_json()
    prompt=recipePromptGeneration(data)
    print(f"generateRecipe {data=}\n")
    
    if "allergic" in prompt:
        prompt=prompt+""" The format is like this example:
{"allergies":"beef","cookware":["Oven","Cooktop"],"ingredients":["1 avocado, sliced","1 cup strawberries, sliced"],"instructions":{"Step-1":"1.step1","Step-2":"2.step2","Step-3":"3.step3","Step-4":"4.step4"},"recipe":"Avocado","time":"15-30minutes"}
The JSON response:"""
    else:
        prompt = prompt + """ The format is like this example:
        {"cookware":["Oven","Cooktop"],"ingredients":["1 avocado, sliced","1 cup strawberries, sliced"],"instructions":{"Step-1":"1.step1","Step-2":"2.step2","Step-3":"3.step3","Step-4":"4.step4"},"recipe":"Avocado","time":"15-30minutes"}
        The JSON response:"""
      
    messages = [{"role": "user", "content": prompt},    {
      'role': 'system',
      'content': 'You are a creative and experienced chef assistant.',
    }]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
    )

    newdata=json.loads(response.choices[0].message.content)

    while("instructions" not in list(newdata.keys())):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        newdata = json.loads(response.choices[0].message.content)
    if "allergic" in prompt:
        newdata["allergies"]=prompt[prompt.find("allergic")+12:prompt.find("I have these cookware")-2]

    return {"prompt":newdata}

def getRecipe(nbrOfResults=1):
    # We will use a json format to send the transaction with all keys: ingredients and allergies.
    json_data_request = request.get_json()
    
    user_specs = tools.stringify_request(json_data_request, request_keys)
    
    # Format prompt request to send to chatgpt
    user_request = tools.generate_ai_prompt_msg(prompt_request, nbrOfResults, user_specs)
    response=generateRecipe(user_request)
    print(response)
    return {"message":response}
