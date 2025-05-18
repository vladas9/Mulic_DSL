import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Any, Optional, Dict, Tuple, Union, cast
import os
import tempfile
from midiutil import MIDIFile
import numpy as np
import sys
import wave

##############################
# LEXER
##############################

class TokenType(Enum):
    # Keywords
    PIANO_TRACK = auto()
    GUITAR_TRACK = auto()
    BASS_TRACK = auto()
    DRUM_TRACK = auto()
    TIME_SIGNATURE = auto()
    TEMPO = auto()
    VOLUME = auto()
    PIANO = auto()
    GUITAR = auto()
    BASS = auto()
    DRUM = auto()
    PAUSE = auto()
    SYNC = auto()
    FOR = auto()
    
    # Special note constants
    SPN_NOTE = auto()
    DRUM_TYPE = auto()
    
    # Identifiers and literals
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    
    # Operators
    EQUALS = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()
    EQUAL_EQUAL = auto()
    NOT_EQUAL = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    MULTIPLY_EQUAL = auto()
    DIVIDE_EQUAL = auto()
    PLUS_PLUS = auto()
    MINUS_MINUS = auto()
    
    # Punctuation
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    SLASH = auto()
    
    # End of file
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        
        # Keywords mapping
        self.keywords: Dict[str, TokenType] = {
            "PianoTrack": TokenType.PIANO_TRACK,
            "GuitarTrack": TokenType.GUITAR_TRACK,
            "BassTrack": TokenType.BASS_TRACK,
            "DrumTrack": TokenType.DRUM_TRACK,
            "TimeSignature": TokenType.TIME_SIGNATURE,
            "Tempo": TokenType.TEMPO,
            "Volume": TokenType.VOLUME,
            "Piano": TokenType.PIANO,
            "Guitar": TokenType.GUITAR,
            "Bass": TokenType.BASS,
            "Drum": TokenType.DRUM,
            "Pause": TokenType.PAUSE,
            "sync": TokenType.SYNC,
            "for": TokenType.FOR,
            # Drum constants
            "KICK": TokenType.DRUM_TYPE,
            "SNARE": TokenType.DRUM_TYPE,
            "HIHAT_CLOSED": TokenType.DRUM_TYPE,
            "HIHAT_OPEN": TokenType.DRUM_TYPE,
            "HIHAT_PEDAL": TokenType.DRUM_TYPE,
            "RIDE": TokenType.DRUM_TYPE,
            "CRASH": TokenType.DRUM_TYPE,
            # Hand positions
            "L": TokenType.IDENTIFIER,
            "R": TokenType.IDENTIFIER,
        }
        
        # Note pattern (e.g., C4, A#3, Db2)
        self.note_pattern = re.compile(r'^[A-G][b#]?\d$')
    
    def scan_tokens(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
            
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens
    
    def is_at_end(self) -> bool:
        return self.current >= len(self.source)
    
    def scan_token(self) -> None:
        c = self.advance()
        
        if c == '(':
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == '{':
            self.add_token(TokenType.LEFT_BRACE)
        elif c == '}':
            self.add_token(TokenType.RIGHT_BRACE)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == '+':
            if self.match('+'):
                self.add_token(TokenType.PLUS_PLUS)
            elif self.match('='):
                self.add_token(TokenType.PLUS_EQUAL)
            else:
                self.add_token(TokenType.PLUS)
        elif c == '-':
            if self.match('-'):
                self.add_token(TokenType.MINUS_MINUS)
            elif self.match('='):
                self.add_token(TokenType.MINUS_EQUAL)
            else:
                self.add_token(TokenType.MINUS)
        elif c == '*':
            if self.match('='):
                self.add_token(TokenType.MULTIPLY_EQUAL)
            else:
                self.add_token(TokenType.MULTIPLY)
        elif c == '/':
            if self.match('='):
                self.add_token(TokenType.DIVIDE_EQUAL)
            elif self.match('/'):
                # A comment goes until the end of the line
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.DIVIDE)
        elif c == '=':
            if self.match('='):
                self.add_token(TokenType.EQUAL_EQUAL)
            else:
                self.add_token(TokenType.EQUALS)
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.LESS_EQUAL)
            else:
                self.add_token(TokenType.LESS_THAN)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.GREATER_EQUAL)
            else:
                self.add_token(TokenType.GREATER_THAN)
        elif c == '!':
            if self.match('='):
                self.add_token(TokenType.NOT_EQUAL)
            else:
                # Handle error: unexpected character
                print(f"Unexpected character at line {self.line}: {c}")
        # Skip whitespace
        elif c in [' ', '\r', '\t']:
            pass
        elif c == '\n':
            self.line += 1
        # String literals
        elif c == '"':
            self.string()
        # Number literals
        elif c.isdigit():
            self.number()
        # Identifiers and keywords
        elif c.isalpha() or c == '_':
            self.identifier()
        else:
            # Handle error: unexpected character
            print(f"Unexpected character at line {self.line}: {c}")
    
    def advance(self) -> str:
        result = self.source[self.current]
        self.current += 1
        return result
    
    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        
        self.current += 1
        return True
    
    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]
    
    def string(self) -> None:
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()
            
        if self.is_at_end():
            # Handle error: unterminated string
            print(f"Unterminated string at line {self.line}")
            return
            
        # Consume the closing "
        self.advance()
        
        # Extract the string value without the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING_LITERAL, value)
    
    def number(self) -> None:
        while self.peek().isdigit():
            self.advance()
            
        # Look for a fractional part
        if self.peek() == '.' and self.peek_next().isdigit():
            # Consume the "."
            self.advance()
            
            while self.peek().isdigit():
                self.advance()
                
            self.add_token(TokenType.FLOAT_LITERAL, float(self.source[self.start:self.current]))
        else:
            self.add_token(TokenType.INT_LITERAL, int(self.source[self.start:self.current]))
    
    def identifier(self) -> None:
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
            
        text = self.source[self.start:self.current]
        
        # Check if it's a note pattern like C4, A#3
        if self.note_pattern.match(text):
            self.add_token(TokenType.SPN_NOTE, text)
            return
        
        # Check if it's a keyword
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type, text if token_type == TokenType.IDENTIFIER else text)
    
    def add_token(self, token_type: TokenType, literal: Any = None) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))


##############################
# AST NODES
##############################

@dataclass
class Expression:
    pass

@dataclass
class Command:
    pass

# Expression types
@dataclass
class Literal(Expression):
    value: Any

@dataclass
class Variable(Expression):
    name: str

@dataclass
class BinaryExpr(Expression):
    left: Expression
    operator: str
    right: Expression

@dataclass
class Grouping(Expression):
    expression: Expression

# Command types
@dataclass
class Assignment(Command):
    name: str
    operator: str
    value: Any

@dataclass
class TimeSignature(Command):
    numerator: int
    denominator: int

@dataclass
class Tempo(Command):
    value: int

@dataclass
class Volume(Command):
    value: str

@dataclass
class Note(Command):
    pass

@dataclass
class PianoNote(Note):
    hand: str
    note: Any
    duration: Any

@dataclass
class GuitarNote(Note):
    string: int
    fret: Any
    duration: Any

@dataclass
class BassNote(Note):
    string: int
    fret: Any
    duration: Any

@dataclass
class DrumNote(Note):
    drum_type: str
    duration: Any

@dataclass
class Pause(Command):
    duration: Any

@dataclass
class SyncBlock(Command):
    commands: List[Command]

@dataclass
class ForLoop(Command):
    var_name: str
    init_value: Any
    condition: Expression
    incr_var: str
    incr_op: str
    incr_value: Any
    body: List[Command]

@dataclass
class Track:
    track_type: str
    commands: List[Command]


##############################
# PARSER
##############################

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.had_error = False
    
    def parse(self) -> List[Track]:
        tracks = []
        
        while not self.is_at_end():
            try:
                if self.check(TokenType.PIANO_TRACK) or self.check(TokenType.GUITAR_TRACK) or \
                   self.check(TokenType.BASS_TRACK) or self.check(TokenType.DRUM_TRACK):
                    tracks.append(self.track())
                else:
                    # Skip tokens until we find a track definition
                    print(f"Unexpected token at line {self.peek().line}: {self.peek().lexeme}")
                    self.advance()
            except ParseError as e:
                self.had_error = True
                print(f"Parse error: {e}")
                self.synchronize()
        
        return tracks
    
    def track(self) -> Track:
        track_type = None
        
        if self.match(TokenType.PIANO_TRACK):
            track_type = "piano"
        elif self.match(TokenType.GUITAR_TRACK):
            track_type = "guitar"
        elif self.match(TokenType.BASS_TRACK):
            track_type = "bass"
        elif self.match(TokenType.DRUM_TRACK):
            track_type = "drum"
        else:
            raise ParseError(f"Expected track definition at line {self.peek().line}")
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after track name")
        
        commands = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            try:
                cmd = self.command()
                if cmd is not None:  # Skip invalid commands
                    commands.append(cmd)
            except ParseError as e:
                print(f"Error in command: {e}")
                self.synchronize_command()
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after track body")
        
        return Track(track_type, commands)
    
    def command(self) -> Optional[Command]:
        try:
            if self.match(TokenType.TIME_SIGNATURE):
                return self.time_signature_command()
            elif self.match(TokenType.TEMPO):
                return self.tempo_command()
            elif self.match(TokenType.VOLUME):
                return self.volume_command()
            elif self.match(TokenType.PIANO):
                return self.note_command("piano")
            elif self.match(TokenType.GUITAR):
                return self.note_command("guitar")
            elif self.match(TokenType.BASS):
                return self.note_command("bass")
            elif self.match(TokenType.DRUM):
                return self.note_command("drum")
            elif self.match(TokenType.PAUSE):
                return self.pause_command()
            elif self.match(TokenType.SYNC):
                return self.sync_block()
            elif self.match(TokenType.FOR):
                return self.for_loop()
            elif self.match(TokenType.IDENTIFIER):
                return self.assignment()
            else:
                raise ParseError(f"Expected command at line {self.peek().line}")
        except ParseError as e:
            # If we hit a semicolon, we can recover
            if self.match(TokenType.SEMICOLON):
                return None
            raise e
    
    def time_signature_command(self) -> TimeSignature:
        self.consume(TokenType.EQUALS, "Expected '=' after TimeSignature")
        numerator = self.consume(TokenType.INT_LITERAL, "Expected numerator value").literal
        self.consume(TokenType.DIVIDE, "Expected '/' in time signature")
        denominator = self.consume(TokenType.INT_LITERAL, "Expected denominator value").literal
        self.consume(TokenType.SEMICOLON, "Expected ';' after time signature")
        
        return TimeSignature(numerator, denominator)
    
    def tempo_command(self) -> Tempo:
        self.consume(TokenType.EQUALS, "Expected '=' after Tempo")
        value = self.consume(TokenType.INT_LITERAL, "Expected tempo value").literal
        self.consume(TokenType.SEMICOLON, "Expected ';' after tempo")
        
        return Tempo(value)
    
    def volume_command(self) -> Volume:
        self.consume(TokenType.EQUALS, "Expected '=' after Volume")
        
        if self.match(TokenType.STRING_LITERAL):
            value = self.previous().literal
        else:
            value = self.consume(TokenType.IDENTIFIER, "Expected volume value").literal
            
        self.consume(TokenType.SEMICOLON, "Expected ';' after volume")
        
        return Volume(value)
    
    def note_command(self, instrument: str) -> Note:
        try:
            self.consume(TokenType.LEFT_PAREN, f"Expected '(' after {instrument}")
            
            if instrument == "piano":
                hand = self.consume(TokenType.IDENTIFIER, "Expected hand position (L/R)").literal
                self.consume(TokenType.COMMA, "Expected ',' after hand position")
                
                if self.match(TokenType.SPN_NOTE):
                    note = self.previous().literal
                else:
                    note = self.consume(TokenType.IDENTIFIER, "Expected note or variable").literal
                    
                self.consume(TokenType.COMMA, "Expected ',' after note")
                duration = self.parse_duration()
                self.consume(TokenType.RIGHT_PAREN, "Expected ')' after piano note")
                self.consume(TokenType.SEMICOLON, "Expected ';' after piano note command")
                
                return PianoNote(hand, note, duration)
            
            elif instrument in ["guitar", "bass"]:
                string = self.consume(TokenType.INT_LITERAL, f"Expected string number for {instrument}").literal
                self.consume(TokenType.COMMA, "Expected ',' after string number")
                
                if self.match(TokenType.INT_LITERAL):
                    fret = self.previous().literal
                else:
                    fret = self.consume(TokenType.IDENTIFIER, "Expected fret number or variable").literal
                    
                self.consume(TokenType.COMMA, "Expected ',' after fret number")
                duration = self.parse_duration()
                self.consume(TokenType.RIGHT_PAREN, f"Expected ')' after {instrument} note")
                self.consume(TokenType.SEMICOLON, f"Expected ';' after {instrument} note command")
                
                if instrument == "guitar":
                    return GuitarNote(string, fret, duration)
                else:  # bass
                    return BassNote(string, fret, duration)
            
            elif instrument == "drum":
                drum_type = self.consume(TokenType.DRUM_TYPE, "Expected drum type").literal
                self.consume(TokenType.COMMA, "Expected ',' after drum type")
                duration = self.parse_duration()
                self.consume(TokenType.RIGHT_PAREN, "Expected ')' after drum note")
                self.consume(TokenType.SEMICOLON, "Expected ';' after drum note command")
                
                return DrumNote(drum_type, duration)
            
            # Default return to satisfy type checker
            raise ParseError(f"Unknown instrument type: {instrument}")
            
        except ParseError as e:
            # Try to recover by skipping to the next semicolon
            while not self.check(TokenType.SEMICOLON) and not self.is_at_end():
                self.advance()
            
            if self.match(TokenType.SEMICOLON):
                # Create a placeholder note
                if instrument == "piano":
                    return PianoNote("R", "C4", 1.0)
                elif instrument == "guitar":
                    return GuitarNote(1, 0, 1.0)
                elif instrument == "bass":
                    return BassNote(1, 0, 1.0)
                elif instrument == "drum":
                    return DrumNote("KICK", 1.0)
            
            # Default return to satisfy type checker
            if instrument == "piano":
                return PianoNote("R", "C4", 1.0)
            elif instrument == "guitar":
                return GuitarNote(1, 0, 1.0)
            elif instrument == "bass":
                return BassNote(1, 0, 1.0)
            else:
                return DrumNote("KICK", 1.0)
    
    def parse_duration(self) -> Any:
        if self.match(TokenType.INT_LITERAL):
            return self.previous().literal
        elif self.match(TokenType.FLOAT_LITERAL):
            return self.previous().literal
        elif self.match(TokenType.IDENTIFIER):
            return self.previous().literal
        elif self.check(TokenType.INT_LITERAL) and self.check_next(TokenType.DIVIDE):
            numerator = self.advance().literal  # Consume the numerator
            self.consume(TokenType.DIVIDE, "Expected '/'")
            denominator = self.consume(TokenType.INT_LITERAL, "Expected denominator").literal
            return numerator / denominator
        else:
            raise ParseError(f"Expected duration at line {self.peek().line}")
    
    def pause_command(self) -> Pause:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after Pause")
        duration = self.parse_duration()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after pause duration")
        self.consume(TokenType.SEMICOLON, "Expected ';' after pause command")
        
        return Pause(duration)
    
    def sync_block(self) -> SyncBlock:
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after sync")
        
        commands = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            try:
                cmd = self.command()
                if cmd is not None:  # Skip invalid commands
                    commands.append(cmd)
            except ParseError as e:
                print(f"Error in sync block: {e}")
                self.synchronize_command()
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after sync block")
        
        return SyncBlock(commands)
    
    def for_loop(self) -> ForLoop:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'")
        
        # Initialization
        if self.match(TokenType.IDENTIFIER):
            var_name = self.previous().lexeme
            self.consume(TokenType.EQUALS, "Expected '=' after variable name")
            
            if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
                init_value = self.previous().literal
            elif self.match(TokenType.SPN_NOTE):
                init_value = self.previous().literal
            elif self.match(TokenType.IDENTIFIER):
                init_value = self.previous().literal
            else:
                raise ParseError(f"Expected expression after '=' at line {self.peek().line}")
        else:
            raise ParseError(f"Expected variable name in for loop initialization at line {self.peek().line}")
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop initialization")
        
        # Condition
        condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop condition")
        
        # Increment
        if self.match(TokenType.IDENTIFIER):
            incr_var = self.previous().lexeme
            
            if self.match(TokenType.PLUS_PLUS):
                incr_op = "++"
                incr_value = 1
            elif self.match(TokenType.MINUS_MINUS):
                incr_op = "--"
                incr_value = 1
            elif self.match(TokenType.PLUS_EQUAL, TokenType.MINUS_EQUAL, TokenType.MULTIPLY_EQUAL, TokenType.DIVIDE_EQUAL):
                incr_op = self.previous().lexeme
                
                if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
                    incr_value = self.previous().literal
                elif self.match(TokenType.IDENTIFIER):
                    incr_value = self.previous().literal
                else:
                    raise ParseError(f"Expected expression after operator at line {self.peek().line}")
            elif self.match(TokenType.EQUALS):
                incr_op = "="
                
                # For complex cases like i = i + 1
                if self.match(TokenType.IDENTIFIER):
                    if self.previous().lexeme == incr_var:  # It's a case like i = i + 1
                        if self.match(TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE):
                            op = self.previous().lexeme
                            
                            if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
                                value = self.previous().literal
                                incr_op = f"{op}="
                                incr_value = value
                            else:
                                raise ParseError(f"Expected literal after operator at line {self.peek().line}")
                        else:
                            raise ParseError(f"Expected operator after variable at line {self.peek().line}")
                    else:
                        # Handle direct assignment of another variable
                        incr_value = self.previous().literal
                else:
                    if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
                        incr_value = self.previous().literal
                    else:
                        raise ParseError(f"Expected expression after '=' at line {self.peek().line}")
            else:
                raise ParseError(f"Expected increment operator at line {self.peek().line}")
        else:
            raise ParseError(f"Expected variable name in for loop increment at line {self.peek().line}")
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after for clauses")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after for header")
        
        body = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            try:
                cmd = self.command()
                if cmd is not None:  # Skip invalid commands
                    body.append(cmd)
            except ParseError as e:
                print(f"Error in for loop body: {e}")
                self.synchronize_command()
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after for body")
        
        return ForLoop(var_name, init_value, condition, incr_var, incr_op, incr_value, body)
    
    def assignment(self) -> Assignment:
        var_name = self.previous().lexeme
        
        if not self.match(TokenType.EQUALS, TokenType.PLUS_EQUAL, TokenType.MINUS_EQUAL, 
                          TokenType.MULTIPLY_EQUAL, TokenType.DIVIDE_EQUAL):
            raise ParseError(f"Expected assignment operator at line {self.peek().line}")
        
        op = self.previous().lexeme
        
        if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            value = self.previous().literal
        elif self.match(TokenType.SPN_NOTE):
            value = self.previous().literal
        elif self.match(TokenType.STRING_LITERAL):
            value = self.previous().literal
        elif self.match(TokenType.IDENTIFIER):
            value = self.previous().literal
        else:
            value = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after assignment")
        
        return Assignment(var_name, op, value)
    
    def expression(self) -> Expression:
        left = self.term()
        
        while self.match(TokenType.PLUS, TokenType.MINUS, 
                         TokenType.LESS_THAN, TokenType.LESS_EQUAL, 
                         TokenType.GREATER_THAN, TokenType.GREATER_EQUAL, 
                         TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL):
            operator = self.previous().lexeme
            right = self.term()
            left = BinaryExpr(left, operator, right)
        
        return left
    
    def term(self) -> Expression:
        left = self.factor()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            operator = self.previous().lexeme
            right = self.factor()
            left = BinaryExpr(left, operator, right)
        
        return left
    
    def factor(self) -> Expression:
        if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            return Literal(self.previous().literal)
        elif self.match(TokenType.SPN_NOTE):
            return Literal(self.previous().literal)
        elif self.match(TokenType.IDENTIFIER):
            return Variable(self.previous().lexeme)
        elif self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return Grouping(expr)
        else:
            raise ParseError(f"Expected expression at line {self.peek().line}")
    
    def match(self, *types) -> bool:
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == token_type
    
    def check_next(self, token_type: TokenType) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type
    
    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF
    
    def peek(self) -> Token:
        return self.tokens[self.current]
    
    def previous(self) -> Token:
        return self.tokens[self.current - 1]
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        
        raise ParseError(f"{message} at line {self.peek().line}")
    
    def synchronize(self) -> None:
        self.advance()
        
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
                
            if self.peek().type in [
                TokenType.PIANO_TRACK, TokenType.GUITAR_TRACK, TokenType.BASS_TRACK, TokenType.DRUM_TRACK,
                TokenType.RIGHT_BRACE
            ]:
                return
                
            self.advance()
    
    def synchronize_command(self) -> None:
        self.advance()
        
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
                
            if self.peek().type in [
                TokenType.TIME_SIGNATURE, TokenType.TEMPO, TokenType.VOLUME,
                TokenType.PIANO, TokenType.GUITAR, TokenType.BASS, TokenType.DRUM,
                TokenType.PAUSE, TokenType.SYNC, TokenType.FOR, TokenType.RIGHT_BRACE,
                TokenType.IDENTIFIER
            ]:
                return
                
            self.advance()


##############################
# INTERPRETER
##############################

# Note to MIDI mapping
NOTE_TO_MIDI = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# Drum kit mapping (General MIDI)
DRUM_TO_MIDI = {
    'KICK': 36,
    'SNARE': 38,
    'HIHAT_CLOSED': 42,
    'HIHAT_OPEN': 46,
    'HIHAT_PEDAL': 44,
    'RIDE': 51,
    'CRASH': 49
}

class Environment:
    def __init__(self):
        self.values: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any) -> None:
        self.values[name] = value
    
    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        raise RuntimeError(f"Undefined variable '{name}'")
    
    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        # Auto-define if not exists
        self.values[name] = value

class MusicEvent:
    def __init__(self, start_time: float, duration: float):
        self.start_time = start_time
        self.duration = duration

class NoteEvent(MusicEvent):
    def __init__(self, start_time: float, duration: float, note_value: int, velocity: int, channel: int):
        super().__init__(start_time, duration)
        self.note_value = note_value
        self.velocity = velocity
        self.channel = channel

class TimeSignatureEvent:
    def __init__(self, time: float, numerator: int, denominator: int):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator

class TempoEvent:
    def __init__(self, time: float, tempo: int):
        self.time = time
        self.tempo = tempo

class Interpreter:
    def __init__(self):
        self.environment = Environment()
        self.events: List[Union[MusicEvent, NoteEvent]] = []
        self.time_signature_events: List[TimeSignatureEvent] = []
        self.tempo_events: List[TempoEvent] = []
        
        # Default settings
        self.current_time = 0.0
        self.current_time_signature = (4, 4)  # 4/4 time
        self.current_tempo = 120  # BPM
        self.current_volume: Dict[str, int] = {
            "piano": 80,  # mf (mezzo-forte)
            "guitar": 80,
            "bass": 80,
            "drum": 80
        }
        
        # Channel mapping
        self.channels: Dict[str, int] = {
            "piano": 0,
            "guitar": 1,
            "bass": 2,
            "drum": 9  # Channel 10 (zero-indexed as 9) is reserved for drums in General MIDI
        }
        
        # Instruments (General MIDI program numbers, 0-indexed)
        self.instruments: Dict[str, int] = {
            "piano": 0,    # Acoustic Grand Piano
            "guitar": 24,  # Acoustic Guitar (nylon)
            "bass": 33     # Electric Bass (finger)
        }
        
        # Volume mapping
        self.volume_mapping: Dict[str, Union[int, str]] = {
            "ppp": 16,     # pianississimo
            "pp": 32,      # pianissimo
            "p": 48,       # piano
            "mp": 64,      # mezzo-piano
            "mf": 80,      # mezzo-forte
            "f": 96,       # forte
            "ff": 112,     # fortissimo
            "fff": 127,    # fortississimo
            "diminuendo": "diminuendo"  # Special case - volume decreases over time
        }
    
    def interpret(self, tracks: List[Track]) -> None:
        for track in tracks:
            # Reset environment for each track
            self.environment = Environment()
            
            # Set initial track environment
            self.current_time = 0.0
            self.current_time_signature = (4, 4)
            
            # Process track commands
            for command in track.commands:
                try:
                    self.execute_command(command, track.track_type)
                except Exception as e:
                    print(f"Error executing command: {e}")
    
    def execute_command(self, command: Command, track_type: str) -> None:
        if isinstance(command, TimeSignature):
            self.time_signature_events.append(
                TimeSignatureEvent(self.current_time, command.numerator, command.denominator)
            )
            self.current_time_signature = (command.numerator, command.denominator)
        
        elif isinstance(command, Tempo):
            self.tempo_events.append(TempoEvent(self.current_time, command.value))
            self.current_tempo = command.value
        
        elif isinstance(command, Volume):
            if command.value in self.volume_mapping:
                vol_value = self.volume_mapping[command.value]
                if vol_value == "diminuendo":
                    # Special case - we'll handle diminuendo during note generation
                    pass
                else:
                    self.current_volume[track_type] = cast(int, vol_value)
            else:
                # If not recognized, use a default value
                self.current_volume[track_type] = 80  # mf
        
        elif isinstance(command, PianoNote):
            duration = self.evaluate_duration(command.duration)
            note_value = self.evaluate_note(command.note)
            
            # Add note event
            self.events.append(
                NoteEvent(
                    self.current_time, 
                    duration, 
                    note_value, 
                    self.current_volume["piano"], 
                    self.channels["piano"]
                )
            )
            
            # Move time forward
            self.current_time += duration
        
        elif isinstance(command, GuitarNote) or isinstance(command, BassNote):
            instrument = "guitar" if isinstance(command, GuitarNote) else "bass"
            duration = self.evaluate_duration(command.duration)
            
            # Convert string and fret to MIDI note
            string_number = command.string
            if isinstance(command.fret, str):
                if command.fret in self.environment.values:
                    fret = self.environment.get(command.fret)
                else:
                    fret = 0  # Default to open string if variable not found
            else:
                fret = command.fret
            
            # Guitar strings from low to high: E2, A2, D3, G3, B3, E4 (standard tuning)
            # Bass strings from low to high: E1, A1, D2, G2 (standard tuning)
            if instrument == "guitar":
                base_notes = [40, 45, 50, 55, 59, 64]  # E2, A2, D3, G3, B3, E4
            else:  # bass
                base_notes = [28, 33, 38, 43]  # E1, A1, D2, G2
            
            # Adjust for 1-indexed strings
            string_idx = min(string_number - 1, len(base_notes) - 1)  # Ensure within range
            note_value = base_notes[string_idx] + fret
            
            # Add note event
            self.events.append(
                NoteEvent(
                    self.current_time, 
                    duration, 
                    note_value, 
                    self.current_volume[instrument], 
                    self.channels[instrument]
                )
            )
            
            # Move time forward
            self.current_time += duration
        
        elif isinstance(command, DrumNote):
            duration = self.evaluate_duration(command.duration)
            
            # Get MIDI note for drum type
            if command.drum_type in DRUM_TO_MIDI:
                note_value = DRUM_TO_MIDI[command.drum_type]
            else:
                print(f"Unknown drum type: {command.drum_type}, using KICK as default")
                note_value = DRUM_TO_MIDI["KICK"]
            
            # Add drum event
            self.events.append(
                NoteEvent(
                    self.current_time, 
                    duration, 
                    note_value, 
                    self.current_volume["drum"], 
                    self.channels["drum"]
                )
            )
            
            # Move time forward
            self.current_time += duration
        
        elif isinstance(command, Pause):
            duration = self.evaluate_duration(command.duration)
            self.current_time += duration
        
        elif isinstance(command, SyncBlock):
            # Save the current time
            start_time = self.current_time
            max_duration = 0.0
            
            # Process each command in the sync block
            for sync_command in command.commands:
                # Reset time to start of sync block for each command
                self.current_time = start_time
                
                # Execute the command
                self.execute_command(sync_command, track_type)
                
                # Track the maximum time advance
                command_duration = self.current_time - start_time
                max_duration = max(max_duration, command_duration)
            
            # Set time to end of the longest command
            self.current_time = start_time + max_duration
        
        elif isinstance(command, ForLoop):
            # Initialize the loop variable
            if isinstance(command.init_value, str):
                if re.match(r'^[A-G][b#]?\d$', command.init_value):  # It's a note
                    self.environment.define(command.var_name, command.init_value)
                else:  # It's a variable
                    if command.init_value in self.environment.values:
                        init_value = self.environment.get(command.init_value)
                    else:
                        init_value = 0  # Default if variable not found
                    self.environment.define(command.var_name, init_value)
            else:  # It's a literal
                self.environment.define(command.var_name, command.init_value)
            
            # Loop while condition is true
            max_iterations = 1000  # Safety limit
            iterations = 0
            
            try:
                while iterations < max_iterations and self.evaluate(command.condition):
                    # Execute the body
                    for body_command in command.body:
                        self.execute_command(body_command, track_type)
                    
                    # Perform the increment
                    self.perform_increment(command.incr_var, command.incr_op, command.incr_value)
                    iterations += 1
                    
                if iterations >= max_iterations:
                    print(f"Warning: Loop exceeded maximum iterations at position {self.current_time}")
            except Exception as e:
                print(f"Error in for loop execution: {e}")
        
        elif isinstance(command, Assignment):
            try:
                if command.operator == "=":
                    if isinstance(command.value, Expression):
                        value = self.evaluate(command.value)
                    elif isinstance(command.value, str):
                        if re.match(r'^[A-G][b#]?\d$', command.value):  # It's a note
                            value = command.value
                        elif command.value in self.environment.values:  # It's a variable
                            value = self.environment.get(command.value)
                        else:
                            value = command.value  # Treat as string
                    else:  # It's a literal
                        value = command.value
                        
                    self.environment.assign(command.name, value)
                else:
                    # Handle other operators (+=, -=, etc.)
                    if command.name in self.environment.values:
                        current_value = self.environment.get(command.name)
                    else:
                        current_value = 0  # Default if not defined
                        
                    if command.operator == "+=":
                        value = current_value + self.evaluate_value(command.value)
                    elif command.operator == "-=":
                        value = current_value - self.evaluate_value(command.value)
                    elif command.operator == "*=":
                        value = current_value * self.evaluate_value(command.value)
                    elif command.operator == "/=":
                        value = current_value / self.evaluate_value(command.value)
                    else:
                        raise RuntimeError(f"Unsupported operator: {command.operator}")
                        
                    self.environment.assign(command.name, value)
            except Exception as e:
                print(f"Error in assignment: {e}")
    
    def evaluate_duration(self, duration: Any) -> float:
        if isinstance(duration, (int, float)):
            return float(duration)
        elif isinstance(duration, str):
            if duration in self.environment.values:
                return float(self.environment.get(duration))
            try:
                return float(duration)
            except ValueError:
                print(f"Invalid duration: {duration}, using 1.0 as default")
                return 1.0
        else:
            print(f"Unexpected duration type: {type(duration)}, using 1.0 as default")
            return 1.0
    
    def evaluate_note(self, note: Any) -> int:
        if isinstance(note, str):
            if note in self.environment.values:
                return self.environment.get(note)
            
            # Parse Scientific Pitch Notation (e.g., C4, A#3)
            match = re.match(r'([A-G][b#]?)(\d+)', note)
            if match:
                note_name, octave = match.groups()
                # Calculate MIDI note number
                note_value = NOTE_TO_MIDI[note_name] + (int(octave) + 1) * 12
                return note_value
            else:
                print(f"Invalid note format: {note}, using C4 (60) as default")
                return 60  # C4
        else:
            return note
    
    def evaluate_value(self, value: Any) -> Any:
        if isinstance(value, Expression):
            return self.evaluate(value)
        elif isinstance(value, str):
            if re.match(r'^[A-G][b#]?\d$', value):  # It's a note
                return self.evaluate_note(value)
            elif value in self.environment.values:  # It's a variable
                return self.environment.get(value)
            else:
                try:
                    # Try to convert to number if possible
                    return float(value)
                except ValueError:
                    return value
        else:  # It's a literal
            return value
    
    def evaluate(self, expr: Expression) -> Any:
        if isinstance(expr, Literal):
            return expr.value
        elif isinstance(expr, Variable):
            if expr.name in self.environment.values:
                return self.environment.get(expr.name)
            else:
                print(f"Undefined variable: {expr.name}, using 0 as default")
                return 0
        elif isinstance(expr, BinaryExpr):
            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)
            
            if expr.operator == "+":
                return left + right
            elif expr.operator == "-":
                return left - right
            elif expr.operator == "*":
                return left * right
            elif expr.operator == "/":
                return left / right
            elif expr.operator == "<":
                return left < right
            elif expr.operator == "<=":
                return left <= right
            elif expr.operator == ">":
                return left > right
            elif expr.operator == ">=":
                return left >= right
            elif expr.operator == "==":
                return left == right
            elif expr.operator == "!=":
                return left != right
            else:
                raise RuntimeError(f"Unknown operator: {expr.operator}")
        elif isinstance(expr, Grouping):
            return self.evaluate(expr.expression)
        else:
            raise RuntimeError(f"Unknown expression type: {expr}")
    
    def perform_increment(self, var_name: str, operator: str, value: Any) -> None:
        try:
            if var_name in self.environment.values:
                current_value = self.environment.get(var_name)
            else:
                current_value = 0  # Default if not defined
                self.environment.define(var_name, current_value)
            
            if operator == "++":
                self.environment.assign(var_name, current_value + 1)
            elif operator == "--":
                self.environment.assign(var_name, current_value - 1)
            elif operator == "+=":
                self.environment.assign(var_name, current_value + self.evaluate_value(value))
            elif operator == "-=":
                self.environment.assign(var_name, current_value - self.evaluate_value(value))
            elif operator == "*=":
                self.environment.assign(var_name, current_value * self.evaluate_value(value))
            elif operator == "/=":
                self.environment.assign(var_name, current_value / self.evaluate_value(value))
            elif operator == "=":
                # For direct assignment in for loops
                self.environment.assign(var_name, self.evaluate_value(value))
            else:
                print(f"Unknown increment operator: {operator}, using simple increment")
                self.environment.assign(var_name, current_value + 1)
        except Exception as e:
            print(f"Error in increment: {e}")
    
    def generate_midi(self, filename: str) -> None:
        # Create MIDIFile with correct tracks
        # Use a simple approach: one track per channel
        num_tracks = 4  # piano, guitar, bass, drum
        midi = MIDIFile(num_tracks)
        
        # Set up instruments for each track
        track_map = {
            0: {"name": "piano", "channel": 0, "program": 0},
            1: {"name": "guitar", "channel": 1, "program": 24},
            2: {"name": "bass", "channel": 2, "program": 33},
            3: {"name": "drum", "channel": 9, "program": None}  # Drums don't need program change
        }
        
        # Set instruments for each track
        for track_num, track_info in track_map.items():
            if track_info["program"] is not None:  # Skip drums
                # Changed from named parameters to positional parameters
                # Order: tracknum, channel, time, program
                midi.addProgramChange(track_num, track_info["channel"], 0, track_info["program"])
        
        # Add tempo events
        if self.tempo_events:
            for tempo_event in self.tempo_events:
                midi.addTempo(0, self.time_to_beats(tempo_event.time), tempo_event.tempo)
        else:
            # Default tempo if none specified
            midi.addTempo(0, 0, 120)
        
        # Add note events
        for event in self.events:
            if isinstance(event, NoteEvent):
                # Map channel to track
                track = event.channel
                if track == 9:  # Drum channel
                    track = 3  # Use track 3 for drums
                
                # Convert to beats
                start_time_beats = self.time_to_beats(event.start_time)
                duration_beats = self.duration_to_beats(event.duration, event.start_time)
                
                # Ensure non-negative duration
                if duration_beats <= 0:
                    duration_beats = 0.25  # Default to a sixteenth note
                
                # Add note to MIDI file - using positional parameters
                try:
                    # Order: track, channel, pitch, time, duration, volume
                    midi.addNote(
                        track,
                        event.channel,
                        event.note_value,
                        start_time_beats,
                        duration_beats,
                        event.velocity
                    )
                except Exception as e:
                    print(f"Error adding note: {e}")
                    print(f"Track: {track}, Channel: {event.channel}, Pitch: {event.note_value}")
                    print(f"Time: {start_time_beats}, Duration: {duration_beats}")
        
        # Write the MIDI file
        with open(filename, "wb") as output_file:
            midi.writeFile(output_file)
    
    def time_to_beats(self, time: float) -> float:
        # Simple conversion using current tempo
        return time * self.current_tempo / 60.0
    
    def duration_to_beats(self, duration: float, start_time: float) -> float:
        # Simple conversion using current tempo
        return duration * self.current_tempo / 60.0
    
    def synthesize_basic_wav(self, wav_file_path: str) -> None:
        """Generate a WAV file with clearly audible tones"""
        # Basic parameters
        sample_rate = 44100
        max_amplitude = 32767  # 16-bit
        
        # Create an empty audio buffer
        duration = max((event.start_time + event.duration for event in self.events 
                    if isinstance(event, NoteEvent)), default=10.0)  # Default duration if no events
        num_samples = int(duration * sample_rate)
        audio_data = np.zeros(num_samples, dtype=np.float32)
        
        # Generate waveforms for each note
        for event in self.events:
            if isinstance(event, NoteEvent):
                start_sample = int(event.start_time * sample_rate)
                end_sample = int((event.start_time + event.duration) * sample_rate)
                
                if start_sample >= num_samples:
                    continue
                
                end_sample = min(end_sample, num_samples)
                sample_count = end_sample - start_sample
                
                if sample_count <= 0:
                    continue  # Skip empty notes
                    
                # Get frequency from MIDI note
                frequency = 440.0 * (2.0 ** ((event.note_value - 69) / 12.0))
                
                # Generate samples - use a mix of sine wave and sawtooth for more presence
                t = np.linspace(0, event.duration, sample_count, endpoint=False)
                
                # Different waveform based on instrument type
                if event.channel == 9:  # Drums
                    # Percussion sounds - more noise components
                    if event.note_value == 36:  # Kick
                        # Low frequency sine with quick decay
                        signal = np.sin(2.0 * np.pi * frequency * t) + 0.5 * np.sin(2.0 * np.pi * (frequency/2) * t)
                        envelope = np.exp(-5 * t/event.duration)
                    elif event.note_value == 38:  # Snare
                        # Mix of sine and noise
                        noise = np.random.uniform(-0.5, 0.5, size=sample_count)
                        signal = 0.5 * np.sin(2.0 * np.pi * frequency * t) + 0.5 * noise
                        envelope = np.exp(-8 * t/event.duration)
                    else:  # Other percussion
                        # Mostly noise with some tone
                        noise = np.random.uniform(-0.7, 0.7, size=sample_count)
                        signal = 0.3 * np.sin(2.0 * np.pi * frequency * t) + 0.7 * noise
                        envelope = np.exp(-10 * t/event.duration)
                elif event.channel == 0:  # Piano
                    # Rich harmonics for piano
                    signal = np.sin(2.0 * np.pi * frequency * t)
                    signal += 0.5 * np.sin(2.0 * np.pi * 2 * frequency * t)  # 1st harmonic
                    signal += 0.3 * np.sin(2.0 * np.pi * 3 * frequency * t)  # 2nd harmonic
                    
                    # Piano-like envelope with sharp attack and gradual decay
                    attack = int(0.01 * sample_count)
                    decay = sample_count - attack
                    envelope = np.ones(sample_count)
                    if attack > 0:
                        envelope[:attack] = np.linspace(0, 1, attack)
                    if decay > 0:
                        envelope[attack:] = np.exp(-3 * np.linspace(0, 1, decay))
                elif event.channel == 1:  # Guitar
                    # Guitar-like sound with rich harmonics
                    signal = np.sin(2.0 * np.pi * frequency * t)
                    signal += 0.5 * np.sin(2.0 * np.pi * 2 * frequency * t)  # 1st harmonic
                    signal += 0.2 * np.sin(2.0 * np.pi * 3 * frequency * t)  # 2nd harmonic
                    
                    # Add slight distortion for character
                    signal = np.tanh(1.5 * signal)
                    
                    # Guitar-like envelope with quick attack and longer sustain
                    attack = int(0.005 * sample_count)
                    decay = int(0.1 * sample_count)
                    sustain = sample_count - attack - decay
                    
                    envelope = np.ones(sample_count)
                    if attack > 0:
                        envelope[:attack] = np.linspace(0, 1, attack)
                    if decay > 0 and sustain > 0:
                        envelope[attack:attack+decay] = np.linspace(1, 0.7, decay)
                        envelope[attack+decay:] = np.linspace(0.7, 0.5, sustain)
                elif event.channel == 2:  # Bass
                    # Bass sound with more fundamental and less harmonics
                    signal = np.sin(2.0 * np.pi * frequency * t)
                    signal += 0.3 * np.sin(2.0 * np.pi * 2 * frequency * t)  # 1st harmonic
                    
                    # Add some warmth with soft clipping
                    signal = np.tanh(1.2 * signal)
                    
                    # Bass-like envelope with medium attack and long sustain
                    attack = int(0.01 * sample_count)
                    decay = int(0.1 * sample_count)
                    sustain = sample_count - attack - decay
                    
                    envelope = np.ones(sample_count)
                    if attack > 0:
                        envelope[:attack] = np.linspace(0, 1, attack)
                    if decay > 0 and sustain > 0:
                        envelope[attack:attack+decay] = np.linspace(1, 0.8, decay)
                        envelope[attack+decay:] = np.linspace(0.8, 0.6, sustain)
                else:
                    # Default instrument sound
                    signal = np.sin(2.0 * np.pi * frequency * t)
                    envelope = np.exp(-3 * t/event.duration)
                
                # Apply velocity scaling
                velocity_factor = event.velocity / 127.0
                
                # Apply envelope and velocity
                samples = signal * envelope * velocity_factor
                
                # Scale to avoid clipping
                samples = samples * 0.5
                
                # Add to audio buffer
                audio_data[start_sample:end_sample] += samples
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.9  # Leave some headroom
        
        # Apply a gentle limiter to prevent clipping
        audio_data = np.tanh(audio_data)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * max_amplitude).astype(np.int16)
        
        # Write WAV file
        with wave.open(wav_file_path, 'w') as wav_file_obj:
            wav_file_obj.setnchannels(1)  # Mono
            wav_file_obj.setsampwidth(2)  # 16-bit
            wav_file_obj.setframerate(sample_rate)
            wav_file_obj.writeframes(audio_data.tobytes())
    
    def convert_midi_to_mp3(self, midi_file: str, mp3_file: str) -> None:
        """
        Convert a MIDI file to MP3 using direct synthesis
        """
        # Generate a WAV file directly from our events
        temp_wav = tempfile.mktemp(suffix=".wav")
        
        try:
            print("Generating audio...")
            self.synthesize_basic_wav(temp_wav)
            
            # Try to convert WAV to MP3 if pydub is available
            try:
                from pydub import AudioSegment
                print(f"Converting WAV to MP3...")
                audio = AudioSegment.from_file(temp_wav, format="wav")
                
                # Normalize and boost volume to ensure audibility
                audio = audio.normalize()
                audio = audio + 6  # Add 6 dB of gain
                
                # Export to MP3
                audio.export(mp3_file, format="mp3", bitrate="192k")
                print(f"Successfully generated MP3 file: {mp3_file}")
            except ImportError:
                print("pydub not available, using WAV instead")
                # Copy the WAV file instead
                import shutil
                wav_output = mp3_file.replace(".mp3", ".wav")
                shutil.copy(temp_wav, wav_output)
                print(f"Generated WAV file instead: {wav_output}")
            except Exception as e:
                print(f"Error converting to MP3: {e}")
                # Fall back to keeping the WAV file
                import shutil
                wav_output = mp3_file.replace(".mp3", ".wav")
                shutil.copy(temp_wav, wav_output)
                print(f"Provided WAV file instead: {wav_output}")
        except Exception as e:
            print(f"Error in audio synthesis: {e}")
            # Just keep the MIDI file
            print(f"Audio synthesis failed. Generated MIDI file only: {midi_file}")
        finally:
            # Clean up temp files
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass


##############################
# MAIN SCRIPT
##############################

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python music_dsl.py <input_file>")
        return
        
    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"Input file not found: {input_file}")
        return
        
    try:
        with open(input_file, 'r') as f:
            source = f.read()
            
        # Create lexer and tokenize the source
        print("Tokenizing source code...")
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        
        # Create parser and parse tokens into AST
        print("Parsing tokens into AST...")
        parser = Parser(tokens)
        tracks = parser.parse()
        
        if not tracks:
            print("No valid tracks found in the input file.")
            return
        
        print(f"Successfully parsed {len(tracks)} tracks")
            
        if parser.had_error:
            print("Parsing had errors but will continue with interpretation.")
        
        # Create interpreter and interpret AST
        print("Interpreting the music...")
        interpreter = Interpreter()
        interpreter.interpret(tracks)
        
        # Generate MIDI file
        print("Generating MIDI file...")
        midi_file = os.path.splitext(input_file)[0] + ".mid"
        interpreter.generate_midi(midi_file)
        print(f"Generated MIDI file: {midi_file}")
        
        # Convert MIDI to MP3
        print("Converting to MP3...")
        mp3_file = os.path.splitext(input_file)[0] + ".mp3"
        interpreter.convert_midi_to_mp3(midi_file, mp3_file)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
