import argparse
import speech_recognition as sr
import requests
import os
import sys
import subprocess
from openai import OpenAI
import re

client = OpenAI(api_key='#api token')


def generate_kubernetes_command(user_input):
    # Call the OpenAI API to generate Kubernetes command based on user input
    completions = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "I need to be provided with Kubernetes commands. Only respond with command as plain text without command syntax."},
            {"role": "user", "content": user_input}
        ]
    )
    command = completions.choices[0].message.content.strip()
    return command


def generate_terraform_code(user_input):    
  completions = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "I need to be provided with only terraform files. Only respond with code as plain text without code block syntax around it."},
      {"role": "user", "content": user_input}
    ]
  )
  message_content = completions.choices[0].message.content
  return message_content


# Write the message_content to file.tf
def write_to_file(message_content):
  with open("file.tf", "w") as file:
      file.write(message_content)

def chat_k8s_ai(args_dict):
    user_input = args_dict['input']
    kubernetes_command = generate_kubernetes_command(user_input)
    print("Generated Kubernetes command:")
    print(kubernetes_command)

    apply_k8s = input("Do you want to execute this Kubernetes command? (yes/no): ")
    if apply_k8s.lower() == 'yes':
        # Optionally write the command to a file
        # write_to_file(kubernetes_command)

        # Execute the Kubernetes command
        subprocess.run(kubernetes_command)
    else:
        print("Kubernetes command execution was cancelled.")

def voice_k8s_ai(args_dict):
    openaiurl = "https://api.openai.com/v1"
    openai_token = '#api token'

    if openai_token == "":
        print("OpenAI API key is not provided.")
        return

    headers = {"Authorization": f"Bearer {openai_token}"}

    print("[-] Record audio using microphone")

    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Say something!")
        audio = r.listen(source)

    folder = "./audio"
    filename = "k8s-results"
    audio_file_path = f"{folder}/{filename}.wav"

    if not os.path.exists(folder):
        os.mkdir(folder)

    print(f"Generating WAV file, saving at location: {audio_file_path}")
    with open(audio_file_path, "wb") as f:
        f.write(audio.get_wav_data())

    print("[-] Call to OpenAI API to transcribe speech to text")

    url = f"{openaiurl}/audio/transcriptions"

    data = {
        "model": "whisper-1",
        "file": audio_file_path,
    }
    files = {
        "file": open(audio_file_path, "rb")
    }

    response = requests.post(url, files=files, data=data, headers=headers)

    print("Status Code:", response.status_code)
    if response.status_code == 200:
        speech_to_text = response.json()["text"]
        print("Speech to text result:", speech_to_text)


        # Generate Kubernetes command based on the speech to text result
        kubernetes_command = generate_kubernetes_command(speech_to_text)
        print("Generated Kubernetes command:")
        print(f'----------- KUBERNETES COMMANDS:{kubernetes_command}--------------')

        # Execute each Kubernetes command

        try:
            subprocess.run(kubernetes_command)  # Execute the command
        except subprocess.CalledProcessError as e:
            print(f"Error executing Kubernetes command: {e}")

        return speech_to_text, kubernetes_command  # Return both speech to text and Kubernetes command
    else:
        print("Failed to transcribe speech to text.")
        return None, None



def chat_tf_ai(args_dict):
    user_input = args_dict['input']  # Access 'input' from args_dict
    terraform_code = generate_terraform_code(user_input)
    print("Generated Terraform code:")
    print(terraform_code)

    apply_tf = input("Do you want to apply this Terraform code? (yes/no): ")
    if apply_tf.lower() == 'yes':
        write_to_file(terraform_code)
        subprocess.run(["terraform", "init"])
        subprocess.run(["terraform", "apply"])
    else:
        print("Terraform code was cancelled.")

def voice_tf_ai(args_dict):
    openaiurl = "https://api.openai.com/v1"
    openai_token = '#api token'

    if openai_token == "":
        print("OpenAI API key is not provided.")
        return

    headers = {"Authorization": f"Bearer {openai_token}"}

    print("[-] Record audio using microphone")

    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Say something!")
        audio = r.listen(source)

    folder = "./audio"
    filename = "tf-results"
    audio_file_path = f"{folder}/{filename}.wav"

    if not os.path.exists(folder):
        os.mkdir(folder)
    
    print(f"Generating WAV file, saving at location: {audio_file_path}")
    with open(audio_file_path, "wb") as f:
        f.write(audio.get_wav_data())

    print("[-] Call to Whisper API's to get the STT response")

    url = f"{openaiurl}/audio/transcriptions"

    data = {
        "model": "whisper-1",
        "file": audio_file_path,
    }
    files = {
        "file": open(audio_file_path, "rb")
    }

    response = requests.post(url, files=files, data=data, headers=headers)

    print("Status Code", response.status_code)
    speech_to_text = response.json()["text"]
    print("Response from Whisper API's", speech_to_text)
    
    terraform_code = generate_terraform_code(speech_to_text)
    print("Generated Terraform code:")
    print(terraform_code)

    with open("file.tf", "w") as f:
        f.write(terraform_code)

    return speech_to_text, terraform_code

def main():
    parser = argparse.ArgumentParser(description="CLI for tf-ai and k8s-ai")
    subparsers = parser.add_subparsers(dest="command", help="Choose between tf-ai and k8s-ai")

    # Subparser for tf-ai & k8s-ai
    tf_ai_parser = subparsers.add_parser("tf-ai", help="Options for tf-ai")
    tf_ai_subparsers = tf_ai_parser.add_subparsers(dest="tf_ai_command", help="Choose between chat and voice")

    k8s_ai_parser = subparsers.add_parser("k8s-ai", help="Options for k8s-ai")
    k8s_ai_subparser = k8s_ai_parser.add_subparsers(dest="k8s_ai_command", help="Choose between chat and voice")

    chat_tf_ai_parser = tf_ai_subparsers.add_parser("chat", help="Chat function for tf-ai")
    chat_tf_ai_parser.add_argument("input", help="Input for the chat function")
    chat_tf_ai_parser.set_defaults(func=chat_tf_ai)

    chat_k8s_ai_parser = k8s_ai_subparser.add_parser("chat", help="Chat function for k8s-ai")
    chat_k8s_ai_parser.add_argument("input", help="Input for the chat fucntion")
    chat_k8s_ai_parser.set_defaults(func=chat_k8s_ai)

    voice_tf_ai_parser = tf_ai_subparsers.add_parser("voice", help="Voice function for tf-ai")
    voice_tf_ai_parser.set_defaults(func=voice_tf_ai)

    voice_k8s_ai_parser = k8s_ai_subparser.add_parser("voice", help="Voice function for k8s-ai")
    voice_k8s_ai_parser.set_defaults(func=voice_k8s_ai)


    args = parser.parse_args()
    if hasattr(args, "func"):
        args_dict = vars(args)
        args.func(args_dict)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


