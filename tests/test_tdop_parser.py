#!/usr/bin/env python
#
# Copyright (c), 2018-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
import unittest
import re
from collections import namedtuple
from textwrap import dedent

from elementpath.tdop import symbol_to_identifier, ParseError, Token, \
    ParserMeta, Parser, MultiLabel


FakeToken = namedtuple('Token', 'symbol pattern label')


def create_fake_tokens(symbols):
    return {s: FakeToken(s, s, 'label') for s in symbols}


class TdopParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        class ExpressionParser(Parser):
            SYMBOLS = {'(integer)', '+', '-', '(name)', '(end)', '(invalid)', '(unknown)'}

            @classmethod
            def create_tokenizer(cls, symbol_table):
                return re.compile(
                    r'INCOMPATIBLE | (\d+)| (UNKNOWN|[+\-]) | '
                    r'(\w+(?=\s+\((?!:))) | (\w+) | (\S) | \s+',
                    flags=re.VERBOSE
                )

        ExpressionParser.literal('(integer)')
        ExpressionParser.register('(name)', bp=100, lbp=100)
        ExpressionParser.register('(end)')
        ExpressionParser.register('(invalid)')
        ExpressionParser.register('(unknown)')

        @ExpressionParser.method(ExpressionParser.infix('+', bp=40))
        def evaluate(self, context=None):
            return self[0].evaluate(context) + self[1].evaluate(context)

        @ExpressionParser.method(ExpressionParser.infix('-', bp=40))
        def evaluate(self, context=None):
            return self[0].evaluate(context) - self[1].evaluate(context)

        cls.parser = ExpressionParser()

    def test_multi_label_class(self):
        label = MultiLabel('function', 'constructor function')
        self.assertEqual(label, 'function')
        self.assertEqual(label, 'constructor function')
        self.assertNotEqual(label, 'constructor')
        self.assertNotEqual(label, 'operator')
        self.assertEqual(str(label), 'function__constructor_function')
        self.assertEqual(repr(label), "MultiLabel('function', 'constructor function')")
        self.assertEqual(hash(label), hash(('function', 'constructor function')))

        self.assertIn(label, ['function'])
        self.assertNotIn(label, [])
        self.assertNotIn(label, ['not a function'])
        self.assertNotIn(label, {'function'})  # compares not equality but hash

        self.assertIn('function', label)
        self.assertIn('constructor', label)
        self.assertNotIn('axis', label)

        self.assertTrue(label.startswith('function'))
        self.assertTrue(label.startswith('constructor'))
        self.assertFalse(label.startswith('operator'))
        self.assertTrue(label.endswith('function'))
        self.assertFalse(label.endswith('constructor'))

    def test_symbol_to_identifier_function(self):
        self.assertEqual(symbol_to_identifier('_cat10'), '_cat10')
        self.assertEqual(symbol_to_identifier('&'), 'Ampersand')
        self.assertEqual(symbol_to_identifier('('), 'LeftParenthesis')
        self.assertEqual(symbol_to_identifier(')'), 'RightParenthesis')

        self.assertEqual(symbol_to_identifier('(name)'), 'name')
        self.assertEqual(symbol_to_identifier('(name'), 'LeftParenthesis_name')

        self.assertEqual(symbol_to_identifier('-'), 'HyphenMinus')
        self.assertEqual(symbol_to_identifier('_'), 'LowLine')
        self.assertEqual(symbol_to_identifier('-_'), 'HyphenMinus_LowLine')
        self.assertEqual(symbol_to_identifier('--'), 'HyphenMinus_HyphenMinus')

        self.assertEqual(symbol_to_identifier('my-api-call'), 'my_api_call')
        self.assertEqual(symbol_to_identifier('call-'), 'call_')

    def test_create_tokenizer_method(self):
        pattern = Parser.create_tokenizer(create_fake_tokens(['(name)', 'call', '+']))
        self.assertEqual(pattern.pattern, dedent(r"""
            ('[^']*'|"[^"]*"|(?:\d+|\.\d+)(?:\.\d*)?(?:[Ee][+-]?\d+)?) |       # Literals
            (call|[+]) |  # Symbols
            ([A-Za-z0-9_]+(?=\s*(?:\(\:.*\:\))?\s*\((?!\:))) | # Function calls
            ([A-Za-z0-9_]+) |       # Names
            (\S) |       # Unknown symbols
            \s+          # Skip extra spaces
            """))

        with self.assertRaises(ValueError):
            Parser.create_tokenizer(create_fake_tokens(['(name)', 'wrong pattern', '+']))

        # Check fix for issue #10
        pattern = Parser.create_tokenizer(create_fake_tokens(
            ['(name)', 'call', '+', '{http://www.w3.org/2000/09/xmldsig#}CryptoBinary']
        ))
        self.assertTrue(
            pattern.pattern.split('\n')[2].strip().startswith(
                r"({http://www.w3.org/2000/09/xmldsig\#}"
            )
        )

    def test_tokenizer_items(self):
        self.assertListEqual(self.parser.tokenizer.findall('5 56'),
                             [('5', '', '', '', ''), ('', '', '', '', ''), ('56', '', '', '', '')])
        self.assertListEqual(self.parser.tokenizer.findall('5+56'),
                             [('5', '', '', '', ''), ('', '+', '', '', ''), ('56', '', '', '', '')])
        self.assertListEqual(self.parser.tokenizer.findall('xy'),
                             [('', '', '', 'xy', '')])
        self.assertListEqual(self.parser.tokenizer.findall('5x'),
                             [('5', '', '', '', ''), ('', '', '', 'x', '')])

    def test_incompatible_tokenizer(self):
        with self.assertRaises(RuntimeError) as ec:
            self.parser.parse('INCOMPATIBLE')
        self.assertIn("incompatible tokenizer", str(ec.exception))

    def test_expression(self):
        token = self.parser.parse('10 + 6')
        self.assertEqual(token.evaluate(), 16)

    def test_syntax_errors(self):
        with self.assertRaises(ParseError) as ec:
            self.parser.parse('x')   # with nud()
        self.assertEqual(str(ec.exception), "unexpected name 'x'")

        with self.assertRaises(ParseError) as ec:
            self.parser.parse('5y')  # with led()
        self.assertEqual(str(ec.exception), "unexpected name 'y'")

        with self.assertRaises(ParseError) as ec:
            self.parser.parse('5 5')  # with expected()
        self.assertEqual(str(ec.exception), "unexpected literal 5")

    def test_unused_token_helpers(self):
        token = self.parser.parse('10')
        self.assertIsNone(token.unexpected('+', '-'))

        with self.assertRaises(ParseError) as ec:
            token.unexpected('(integer)')
        self.assertEqual(str(ec.exception), "unexpected literal 10")

        self.assertIsInstance(token.wrong_type(), TypeError)
        self.assertIsInstance(token.wrong_value(), ValueError)

    def test_unknown_symbol(self):
        with self.assertRaises(ParseError) as ec:
            self.parser.parse('?')
        self.assertEqual(str(ec.exception), "unknown symbol '?'")

        with self.assertRaises(ParseError) as ec:
            self.parser.parse('UNKNOWN')
        self.assertEqual(str(ec.exception), "unknown symbol 'UNKNOWN'")

    def test_invalid_source(self):
        with self.assertRaises(ParseError) as ec:
            self.parser.parse(10)
        self.assertIn("invalid source type", str(ec.exception))

    def test_invalid_token(self):
        token = self.parser.symbol_table['(invalid)'](self.parser, '10e')
        self.assertEqual(str(token.wrong_syntax()), "invalid literal '10e'")

    def test_parser_position(self):
        parser = type(self.parser)()
        parser.source = '   7 +\n 8 '
        parser.tokens = iter(parser.tokenizer.finditer(parser.source))
        self.assertIsNone(parser.token)

        parser.advance()
        self.assertIsNone(parser.token)
        self.assertEqual(parser.position, (1, 4))
        self.assertTrue(parser.is_source_start())
        self.assertTrue(parser.is_line_start())
        self.assertFalse(parser.is_spaced())

        parser.advance()
        self.assertIsNotNone(parser.token)
        self.assertEqual(parser.token.value, 7)
        self.assertEqual(parser.position, (1, 4))
        self.assertTrue(parser.is_source_start())
        self.assertTrue(parser.is_line_start())
        self.assertTrue(parser.is_spaced())

        parser.advance()
        self.assertEqual(parser.token.symbol, '+')
        self.assertEqual(parser.position, (1, 6))
        self.assertFalse(parser.is_source_start())
        self.assertFalse(parser.is_line_start())

        parser.advance()
        self.assertEqual(parser.token.value, 8)
        self.assertEqual(parser.position, (2, 2))
        self.assertFalse(parser.is_source_start())
        self.assertTrue(parser.is_line_start())

        self.assertTrue(parser.is_spaced())
        parser.source = '   7 +'
        self.assertFalse(parser.is_spaced())

    def test_advance_until(self):
        parser = type(self.parser)()
        parser.source = ''
        parser.tokens = iter(parser.tokenizer.finditer(parser.source))
        parser.advance()

        with self.assertRaises(TypeError) as ec:
            parser.advance_until()
        self.assertEqual(str(ec.exception), "at least a stop symbol required!")

        with self.assertRaises(ParseError) as ec:
            parser.advance_until('+')
        self.assertEqual(str(ec.exception), "source is empty")

        parser = type(self.parser)()
        parser.source = '5 6 7 + 8'
        parser.tokens = iter(parser.tokenizer.finditer(parser.source))
        parser.advance()
        self.assertEqual(parser.next_token.symbol, '(integer)')
        self.assertEqual(parser.next_token.value, 5)
        parser.advance_until('+')
        self.assertEqual(parser.next_token.symbol, '+')

        parser = type(self.parser)()
        parser.source = '5 6 7 + 8'
        parser.tokens = iter(parser.tokenizer.finditer(parser.source))
        parser.advance()
        self.assertEqual(parser.next_token.symbol, '(integer)')
        self.assertEqual(parser.next_token.value, 5)
        parser.advance_until('*')
        self.assertEqual(parser.next_token.symbol, '(end)')

        parser = type(self.parser)()
        parser.source = '5 UNKNOWN'
        parser.tokens = iter(parser.tokenizer.finditer(parser.source))
        parser.advance()
        self.assertEqual(parser.next_token.symbol, '(integer)')
        self.assertEqual(parser.next_token.value, 5)

        with self.assertRaises(ParseError) as ec:
            parser.advance_until('UNKNOWN')
        self.assertEqual(str(ec.exception), "unknown symbol '(unknown)'")

    def test_unescape_helper(self):
        self.assertEqual(self.parser.unescape("'\\''"), "'")
        self.assertEqual(self.parser.unescape('"\\""'), '"')

    def test_invalid_parser_derivation(self):
        globals()['ExpressionParser'] = self.parser.__class__

        try:
            with self.assertRaises(RuntimeError) as ec:
                class AnotherParser(Parser):
                    pass

                isinstance(AnotherParser, Parser)

            self.assertEqual(str(ec.exception),
                             "Multiple parser class definitions per module are not allowed")
        finally:
            del globals()['ExpressionParser']

    def test_new_parser_class(self):

        class FakeBase:
            pass

        class AnotherParser(FakeBase, metaclass=ParserMeta):
            pass

        self.assertIs(AnotherParser.token_base_class, Token)
        self.assertEqual(AnotherParser.literals_pattern.pattern,
                         r"""'[^']*'|"[^"]*"|(?:\d+|\.\d+)(?:\.\d*)?(?:[Ee][+-]?\d+)?""")

    def test_incomplete_parser_build(self):

        class UnfinishedParser(Parser):
            SYMBOLS = {'(integer)', r'function\(', r'axis\:\:', '(name)', '(end)'}

        UnfinishedParser.literal('(integer)')
        UnfinishedParser.register(r'function\(')
        UnfinishedParser.register(r'axis\:\:')
        UnfinishedParser.register('(end)')

        with self.assertRaises(ValueError) as ec:
            UnfinishedParser.build()
        self.assertIn("unregistered symbols: ['(name)']", str(ec.exception))

    def test_invalid_registrations(self):

        class AnotherParser(Parser):
            SYMBOLS = {'(integer)', r'function\(', '(name)', '(end)'}

        with self.assertRaises(ValueError) as ec:
            AnotherParser.register(r'function \(')
        self.assertIn("a symbol can't contain whitespaces", str(ec.exception))

        with self.assertRaises(NameError) as ec:
            AnotherParser.register('undefined')
        self.assertIn("'undefined' is not a symbol of the parser", str(ec.exception))

    def test_other_operators(self):

        class ExpressionParser(Parser):
            SYMBOLS = {'(integer)', '+', '++', '-', '*', '(end)'}

        ExpressionParser.prefix('++')
        ExpressionParser.postfix('+')

        @ExpressionParser.method(ExpressionParser.prefix('++', bp=90))
        def evaluate(self_, context=None):
            return self_[0].evaluate(context) + 1

        @ExpressionParser.method(ExpressionParser.postfix('+', bp=90))
        def evaluate(self_, context=None):
            return self_[0].evaluate(context) + 1

        @ExpressionParser.method(ExpressionParser.infixr('-', bp=50))
        def evaluate(self_, context=None):
            return self_[0].evaluate(context) - self_[1].evaluate(context)

        @ExpressionParser.method('*', bp=70)
        def nud(self_):
            for _ in range(3):
                self_.append(self_.parser.expression(rbp=70))
            return self_

        @ExpressionParser.method('*', bp=70)
        def evaluate(self_, context=None):
            return self_[0].evaluate(context) * \
                self_[1].evaluate(context) * self_[2].evaluate(context)

        ExpressionParser.literal('(integer)')
        ExpressionParser.register('(end)')

        parser = ExpressionParser()

        token = parser.parse('++5')
        self.assertEqual(token.source, '++ 5')
        self.assertEqual(token.evaluate(), 6)

        token = parser.parse('8 +')
        self.assertEqual(token.source, '8 +')
        self.assertEqual(token.evaluate(), 9)

        token = parser.parse(' 8 -  5')
        self.assertEqual(token.source, '8 - 5')
        self.assertEqual(token.evaluate(), 3)

        token = parser.parse('* 8 2 5')
        self.assertEqual(token.source, '* 8 2 5')
        self.assertEqual(token.evaluate(), 80)


if __name__ == '__main__':
    unittest.main()
