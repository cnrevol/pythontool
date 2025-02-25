import requests
import json
import time
import os
import re

# Define the question ranges with their respective child question counts
# Based on the screenshots provided
MULTI_QUESTION_RANGES = {
    196: 6,  # Question 196 has 6 child questions
    197: 5,  # Question 197 has 5 child questions
    198: 4,  # Based on the pattern
    199: 5,  # Based on the pattern
    200: 7,  # Based on the second screenshot
    201: 7,  # Based on the second screenshot
    202: 6,  # Based on the pattern
    203: 6,  # Based on the pattern
    204: 6,  # Based on the pattern
    205: 5,  # Based on the pattern
    206: 5,  # Based on the pattern
}

def clean_html_and_encoding(text):
    """
    Remove HTML tags, special encoding, and normalize line breaks
    
    Args:
        text (str): Text to clean
    
    Returns:
        str: Cleaned text
    """
    if text is None:
        return ""
    
    # Replace HTML line breaks with actual line breaks
    text = text.replace("<br />", "\n").replace("<br>", "\n")
    
    # Replace HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&rsquo;", "'")
    text = text.replace("&ldquo;", "\"")
    text = text.replace("&rdquo;", "\"")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def fetch_question_data(main_index, child_index=None, library_id="042e86d045354de7a0fc18714586a0c9", auth_token="6fc972642df545ad9704bcdb38520159"):
    """
    Fetch question data from the API
    
    Args:
        main_index (int): The question index to fetch
        child_index (int, optional): The child question index to fetch
        library_id (str): The library ID
        auth_token (str): Authorization token
    
    Returns:
        dict: The JSON response
    """
    # Generate current timestamp
    current_timestamp = int(time.time() * 1000)
    
    # Construct URL (include childIndex if provided)
    url = f"https://ea.qingsuyun.com/h5/api/exercise/list/mainSwatch?mode=1&libraryId={library_id}&mainIndex={main_index}"
    if child_index is not None:
        url += f"&childIndex={child_index}"
    url += f"&practiceId=&pTime={current_timestamp}"
    
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

def extract_question_info(data, main_index, is_child=False, child_index=None):
    """
    Extract question information from the JSON data
    
    Args:
        data (dict): The JSON response
        main_index (int): The main question index
        is_child (bool): Whether this is a child question
        child_index (int, optional): The child question index
    
    Returns:
        dict: Extracted information
    """
    if data is None or data.get("code") != "200":
        return None
    
    body = data.get("body", {})
    
    # If this is a child question, get the child data
    if is_child and "child" in body:
        question_data = body["child"]
        parent_content = clean_html_and_encoding(body.get("questionContent", ""))
    else:
        question_data = body
        parent_content = None
    
    # Use the main_index parameter directly instead of relying on the API response
    question_number = main_index
    
    # For child questions, also store the child index
    if is_child and child_index is not None:
        child_number = child_index
    else:
        child_number = None
    
    # Get question content
    question_content = clean_html_and_encoding(question_data.get("questionContent", "Unknown"))
    
    # Get options
    options = []
    json_data = question_data.get("jsonData", {})
    single_data = json_data.get("single", {})
    
    for option in single_data.get("options", []):
        option_content = clean_html_and_encoding(option.get("optionsContent", ""))
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
        "child_number": child_number,
        "parent_content": parent_content,
        "question_content": question_content,
        "options": options,
        "correct_answer": correct_answer
    }

def save_question_info_to_file(question_info, info_file, is_child=False):
    """
    Append extracted question information to a single text file
    
    Args:
        question_info (dict): Extracted question information
        info_file (file): Open file handle to write to
        is_child (bool): Whether this is a child question
    """
    if question_info:
        # Write parent content for the first child question only
        if is_child and question_info['child_number'] == 1 and question_info['parent_content']:
            info_file.write(f"Common Scenario:\n{question_info['parent_content']}\n\n")
            info_file.write("-" * 50 + "\n\n")
        
        # Write question number and child index if applicable
        if is_child:
            info_file.write(f"Question Number: {question_info['question_number']} (Child {question_info['child_number']})\n")
        else:
            info_file.write(f"Question Number: {question_info['question_number']}\n")
        
        # Write question content
        info_file.write(f"Question Content: {question_info['question_content']}\n\n")
        info_file.write("Options:\n")
        
        # Write options
        for i, option in enumerate(question_info['options']):
            option_letter = chr(65 + i)  # Convert 0 to A, 1 to B, etc.
            info_file.write(f"{option_letter}. {option['content']}\n")
        
        # Write correct answer
        info_file.write(f"\nCorrect Answer: {question_info['correct_answer']}\n")
        
        # Write separator between questions
        if is_child and question_info['child_number'] < MULTI_QUESTION_RANGES.get(question_info['question_number'], 0):
            info_file.write("-" * 50 + "\n\n")  # Separator between child questions
        else:
            info_file.write("=" * 50 + "\n\n")  # Separator between main questions

def main():
    # Create output directory
    output_dir = "question_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Ask user for input
    start_index = int(input("Enter starting question index: "))
    end_index = int(input("Enter ending question index (for a single question, enter the same as start): "))
    
    # Create files for saving data - separate files for multi-question and single-question
    multi_info_filename = f"{output_dir}/multi_questions_info.txt"
    multi_json_filename = f"{output_dir}/multi_questions_raw.json"
    single_info_filename = f"{output_dir}/single_questions_info.txt"
    single_json_filename = f"{output_dir}/single_questions_raw.json"
    
    # Create or clear the information text files
    for filename in [multi_info_filename, single_info_filename]:
        with open(filename, "w", encoding="utf-8") as file:
            pass  # Just create/clear the file
    
    # Dictionaries to hold all raw JSON data
    multi_raw_json = {}
    single_raw_json = {}
    
    # Fetch and process questions
    for main_index in range(start_index, end_index + 1):
        print(f"Processing question {main_index}...")
        
        # Check if this is a multi-question
        child_count = MULTI_QUESTION_RANGES.get(main_index, 0)
        
        if child_count > 0:
            # This is a multi-question, fetch each child question
            multi_raw_json[f"question_{main_index}"] = {}
            
            for child_index in range(1, child_count + 1):
                print(f"  Fetching child question {child_index}...")
                
                # Add a random delay to simulate human behavior (0.5 to 2 seconds)
                delay = 0.5 + 1.5 * (time.time() % 1)
                time.sleep(delay)
                
                # Fetch data
                raw_json = fetch_question_data(main_index, child_index)
                
                if raw_json:
                    # Extract information
                    question_info = extract_question_info(raw_json, main_index, is_child=True, child_index=child_index)
                    
                    # Save extracted info to text file
                    with open(multi_info_filename, "a", encoding="utf-8") as info_file:
                        save_question_info_to_file(question_info, info_file, is_child=True)
                    
                    # Add raw JSON to dictionary
                    multi_raw_json[f"question_{main_index}"][f"child_{child_index}"] = raw_json
                    
                    print(f"  Child question {child_index} processed successfully.")
                else:
                    print(f"  Failed to fetch child question {child_index}.")
        else:
            # This is a single question
            print(f"  Fetching single question...")
            
            # Add a random delay to simulate human behavior (0.5 to 2 seconds)
            delay = 0.5 + 1.5 * (time.time() % 1)
            time.sleep(delay)
            
            # Fetch data
            raw_json = fetch_question_data(main_index)
            
            if raw_json:
                # Extract information
                question_info = extract_question_info(raw_json, main_index)
                
                # Save extracted info to text file
                with open(single_info_filename, "a", encoding="utf-8") as info_file:
                    save_question_info_to_file(question_info, info_file)
                
                # Add raw JSON to dictionary
                single_raw_json[f"question_{main_index}"] = raw_json
                
                print(f"  Question processed successfully.")
            else:
                print(f"  Failed to fetch question.")
    
    # Save all raw JSON data to files
    with open(multi_json_filename, "w", encoding="utf-8") as json_file:
        json.dump(multi_raw_json, json_file, ensure_ascii=False, indent=4)
    
    with open(single_json_filename, "w", encoding="utf-8") as json_file:
        json.dump(single_raw_json, json_file, ensure_ascii=False, indent=4)
    
    print(f"All questions processed.")
    print(f"Multi-question information saved to: {multi_info_filename}")
    print(f"Multi-question raw JSON data saved to: {multi_json_filename}")
    print(f"Single-question information saved to: {single_info_filename}")
    print(f"Single-question raw JSON data saved to: {single_json_filename}")

if __name__ == "__main__":
    main()