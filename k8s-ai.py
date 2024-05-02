import argparse
import speech_recognition as sr
import requests
import os
import sys
import subprocess
from openai import OpenAI

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

def write_to_file(command):
    with open("kubernetes_command.txt", "w") as file:
        file.write(command)

def chat_k8s_ai(args):
    user_input = args.input
    kubernetes_command = generate_kubernetes_command(user_input)
    print("Generated Kubernetes command:")
    print(kubernetes_command)

    apply_k8s = input("Do you want to execute this Kubernetes command? (yes/no): ")
    if apply_k8s.lower() == 'yes':
        # Optionally write the command to a file
        # write_to_file(kubernetes_command)

        # Execute the Kubernetes command
        subprocess.run(kubernetes_command)  # Example command, replace with your own
    else:
        print("Kubernetes command execution was cancelled.")

def voice_kubernetes(args_dict):
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
        return speech_to_text
    else:
        print("Failed to transcribe speech to text.")
        return None

def main():
    parser = argparse.ArgumentParser(description="CLI for Kubernetes command generation")
    subparsers = parser.add_subparsers(dest="command", help="Choose between chat and voice")

    # Subparser for k8s-ai
    k8s_ai_parser = subparsers.add_parser("chat", help="Chat-based interaction")
    k8s_ai_subparser = k8s_ai_parser.add_subparsers(dest="k8s_ai_command", help="Choose between chat and voice")
    
    
    chat_k8s_ai_parser = k8s_ai_subparser.add_parser("chat", help="Chat function for k8s-ai")
    chat_k8s_ai_parser.add_argument("input", help="Input for the chat fucntion")
    chat_k8s_ai_parser.set_defaults(func=chat_k8s_ai)

    # Subparser for voice
    voice_k8s_ai_parser = k8s_ai_subparser.add_parser("voice", help="Voice function for k8s-ai")
    voice_k8s_ai_parser.set_defaults(func=voice_k8s_ai)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
