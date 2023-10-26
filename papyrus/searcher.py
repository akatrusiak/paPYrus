import os
import string
from collections import defaultdict
from nltk.stem import PorterStemmer
from pathlib import Path
from typing import List, Tuple

from config import *



class ScrollSearch:
    def __init__(self, directory: str):
        """
        Initializes the ScrollSearch object.
        
        :param directory: The directory containing text files to be searched.
        """
        self.directory = Path(directory)
        if not self.directory.exists() or not self.directory.is_dir():
            raise ValueError("Provided path is not a valid directory.")
        self.inverted_index = defaultdict(list)  # A dictionary to store the inverted index
        self.files = {}  # A dictionary to store the content of each file
        self.stemmer = PorterStemmer()  # The stemmer used for token normalization
        self.build_index()

    def build_index(self):
        """
        Builds the inverted index from the text files in the specified directory.
        """
        for file_path in self.directory.rglob('*.txt'):
            if file_path.is_file() and file_path.suffix.lower() in FILE_TYPES:
                try:
                    
                    with file_path.open('r') as f:  # Updated to open the file using the Path object
                        content = f.read()
                except Exception as e:
                    print(f"Could not read file {file_path}: {str(e)}")
                    continue
                
                tokens = self.tokenize(content)
                for token in tokens:
                    # Updated to convert the Path object to a string before adding it to the index
                    self.inverted_index[token].append(str(file_path))  
                # Updated to convert the Path object to a string before using it as a key
                self.files[str(file_path)] = content

    def search(self, query, phrase_search: bool = False) -> List[Tuple[str,str]]:
        """
        Searches the indexed text files for the given query.
        
        :param query: The search query.
        :param phrase_search: If True, performs a phrase search. If False, performs a token search.
        :return: A list of tuples, each containing a file path and a preview of the content.
        """
        tokens = self.tokenize(query)
        if not tokens:
            return[]
        
        if phrase_search:
            results = set(self.files.keys())
        else:
            results = set(self.inverted_index[tokens[0]])
        
        for token in tokens[1:]:
            if phrase_search:
                results &= set(self.inverted_index[token])
            else:
                results |= set(self.inverted_index[token])

        
        return [(str(file), self._get_preview(self.files[str(file)], tokens)) for file in results]

    def _token_search(self, tokens):
        """
        Performs a token-based search.
        
        :param tokens: The list of stemmed tokens to search for.
        :return: A set of file paths that contain all of the tokens.
        """
        results = set(self.files.keys())
        for token in tokens:
            results &= set(self.inverted_index[token])
        return results
    
    def _phrase_search(self, tokens, original_phrase):
        """
        Performs a phrase search.
        
        :param tokens: The list of stemmed tokens that make up the phrase.
        :param original_phrase: The original search phrase.
        :return: A set of file paths that contain the phrase.
        """
        results = set()
        for file, content in self.files.items():
            start = 0
            while True:
                start = content.lower().find(original_phrase.lower(), start)
                if start == -1:
                    break
                # Verify that the surrounding context contains the individual stemmed tokens
                end = start + len(original_phrase)
                surrounding_text = content[max(0, start-30):min(len(content), end+30)]
                if all(stemmed_token in self.tokenize(surrounding_text) for stemmed_token in tokens):
                    results.add(file)
                    break  # No need to search for additional occurrences in this file
                start += len(original_phrase)
        return results

    def _get_preview(self, content, tokens):
        """
        Returns a preview of the content where the tokens appear.
        
        :param content: The content of a file.
        :param tokens: The list of stemmed tokens to search for.
        :return: A string containing a preview of the content.
        """
        # Return the first PREVIEW_LENGTH around the token
        start = max(content.lower().find(tokens[0]) - PREVIEW_LENGTH/2, 0)
        end = min(start + PREVIEW_LENGTH, len(content))
        return content[start:end]

    def tokenize(self, text):
        """
        Simple tokenizer that splits text by whitespace and removes punctuation.
        
        :param text: The text to be tokenized.
        :return: A list of stemmed tokens.
        """
        translator = str.maketrans("", "", string.punctuation)
        tokens = text.translate(translator).lower().split()
        stemmed_tokens = [self.stemmer.stem(token) for token in tokens]
        return stemmed_tokens

if __name__ == "__main__":

    test_dir = "../test"

    # Instantiating the ScrollSearch class
    searcher = ScrollSearch(test_dir)

    # Running test queries
    test_queries = {
        'token search (multiple matches)': ('sample text', False),
        'token search (no matches)': ('nonexistent', False),
        'phrase search (match)': ('repeating phrase', True),
        'phrase search (no matches)': ('this should not match anything', True)
    }

    # Executing the queries and printing the results
    results = {}
    for description, (query, phrase_search) in test_queries.items():
        result = searcher.search(query, phrase_search)
        results[description] = result
        print(f"\n{description.capitalize()}:\nQuery: {query}\nResults: {len(result)} files found")
        for file, preview in result:
            print(f"File: {os.path.basename(file)}\nPreview: {preview}\n")

    results
