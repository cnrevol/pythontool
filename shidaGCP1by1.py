import requests
import json
import time
import os

def fetch_question_data(main_index, library_id="042e86d045354de7a0fc18714586a0c9", auth_token="6fc972642df545ad9704bcdb38520159"):
    """
    Fetch question data from the API
    
    Args:
        main_index (int): The question index to fetch
        library_id (str): The library ID
        auth_token (str): Authorization token
    
    Returns:
        dict: The JSON response
    """
    # Generate current timestamp
    current_timestamp = int(time.time() * 1000)
    
    # Construct URL
    url = f"https://ea.qingsuyun.com/h5/api/exercise/list/mainSwatch?mode=1&libraryId={library_id}&mainIndex={main_index}&practiceId=&pTime={current_timestamp}"
    
    # Set headers
    headers = {
        "Authorization": auth_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check if request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Status code {response.status_code}")
        return None

def extract_question_info(data):
    """
    Extract question information from the JSON data
    
    Args:
        data (dict): The JSON response
    
    Returns:
        dict: Extracted information
    """
    if data is None or data.get("code") != "200":
        return None
    
    body = data.get("body", {})
    
    # Get question number
    question_number = body.get("s", "Unknown")
    
    # Get question content
    question_content = body.get("questionContent", "Unknown")
    
    # Get options
    options = []
    json_data = body.get("jsonData", {})
    single_data = json_data.get("single", {})
    
    for option in single_data.get("options", []):
        option_content = option.get("optionsContent", "")
        is_correct = option.get("rightAnswers", False)
        options.append({
            "content": option_content,
            "is_correct": is_correct
        })
    
    # Determine correct answer letter (A, B, C, D)
    correct_answer = ""
    for i, option in enumerate(options):
        if option.get("is_correct"):
            correct_answer += chr(65 + i)  # Convert 0 to A, 1 to B, etc.
    
    return {
        "question_number": question_number,
        "question_content": question_content,
        "options": options,
        "correct_answer": correct_answer
    }

def save_to_files(question_info, raw_json, main_index, output_dir="output"):
    """
    Save extracted information to text files
    
    Args:
        question_info (dict): Extracted question information
        raw_json (dict): Raw JSON data
        main_index (int): Question index
        output_dir (str): Directory to save files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save extracted information to text file
    if question_info:
        with open(f"{output_dir}/question_{main_index}_info.txt", "w", encoding="utf-8") as f:
            f.write(f"Question Number: {question_info['question_number']}\n")
            f.write(f"Question Content: {question_info['question_content']}\n\n")
            f.write("Options:\n")
            
            for i, option in enumerate(question_info['options']):
                option_letter = chr(65 + i)  # Convert 0 to A, 1 to B, etc.
                f.write(f"{option_letter}. {option['content']}\n")
            
            f.write(f"\nCorrect Answer: {question_info['correct_answer']}")
    
    # Save raw JSON to file
    with open(f"{output_dir}/question_{main_index}_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_json, f, ensure_ascii=False, indent=4)

def main():
    # Create output directory
    output_dir = "question_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Ask user for input
    start_index = int(input("Enter starting question index: "))
    end_index = int(input("Enter ending question index (for a single question, enter the same as start): "))
    
    # Fetch and process questions
    for main_index in range(start_index, end_index + 1):
        print(f"Fetching question {main_index}...")
        
        # Add a random delay to simulate human behavior (0.5 to 2 seconds)
        delay = 0.5 + 1.5 * (time.time() % 1)
        time.sleep(delay)
        
        # Fetch data
        raw_json = fetch_question_data(main_index)
        
        if raw_json:
            # Extract information
            question_info = extract_question_info(raw_json)
            
            # Save to files
            save_to_files(question_info, raw_json, main_index, output_dir)
            
            print(f"Question {main_index} saved successfully.")
        else:
            print(f"Failed to fetch question {main_index}.")
    
    print(f"All questions processed. Files saved to '{output_dir}' directory.")

if __name__ == "__main__":
    main()