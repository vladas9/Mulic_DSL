import sys
from lexer import Lexer
from parser import Parser

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <filename>")
        return

    with open(sys.argv[1], 'r') as f:
        data = f.read()

    lexer = Lexer(data)
    parser = Parser(lexer)
    
    try:
        parsed_data = parser.parse()
        print("Parsing successful!")
        print(parsed_data)
        
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
