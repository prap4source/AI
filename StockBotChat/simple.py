from openai import OpenAI
openai = OpenAI(
    api_key='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'
)
response = openai.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {
      "role": "system",
      "content": "You a Stock Analyst"
    },
    {
      "role": "user",
      "content": "Who is the CEO of APPLE"
    }
  ],
  temperature=0.8,
  max_tokens=256,
  top_p=1
)
print(response)