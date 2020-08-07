#
# Copyright (c), 2018-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
"""
XPath 2.0 implementation - part 3 (XSD constructors and multi-role tokens)
"""
from .exceptions import ElementPathError, ElementPathSyntaxError
from .namespaces import XQT_ERRORS_NAMESPACE, XSD_NAMESPACE
from . import datatypes
from .xpath_token import XPathToken
from .xpath_context import XPathSchemaContext
from .xpath2_functions import XPath2Parser


register = XPath2Parser.register
unregister = XPath2Parser.unregister
method = XPath2Parser.method
constructor = XPath2Parser.constructor


###
# Constructors for string-based XSD types
@constructor('normalizedString')
def cast(self, value):
    return datatypes.NormalizedString(value)


@constructor('token')
def cast(self, value):
    try:
        return datatypes.XsdToken(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('language')
def cast(self, value):
    try:
        return datatypes.Language(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('NMTOKEN')
def cast(self, value):
    try:
        return datatypes.NMToken(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('Name')
def cast(self, value):
    try:
        return datatypes.Name(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('NCName')
def cast(self, value):
    try:
        return datatypes.NCName(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('ID')
def cast(self, value):
    try:
        return datatypes.Id(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('IDREF')
def cast(self, value):
    try:
        return datatypes.Idref(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('ENTITY')
def cast(self, value):
    try:
        return datatypes.Entity(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('anyURI')
def cast(self, value):
    try:
        return datatypes.AnyURI(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


###
# Constructors for numeric XSD types
@constructor('decimal')
def cast(self, value):
    try:
        return datatypes.DecimalProxy(value)
    except (ArithmeticError, ValueError) as err:
        if isinstance(value, (str, datatypes.UntypedAtomic)):
            raise self.error('FORG0001', str(err))
        raise self.error('FOCA0002', str(err))


@constructor('double')
def cast(self, value):
    try:
        return datatypes.DoubleProxy(value, self.parser.xsd_version)
    except ValueError as err:
        if isinstance(value, (str, datatypes.UntypedAtomic)):
            raise self.error('FORG0001', str(err))
        raise self.error('FOCA0002', str(err))


@constructor('float')
def cast(self, value):
    try:
        return datatypes.Float(value, self.parser.xsd_version)
    except ValueError as err:
        if isinstance(value, (str, datatypes.UntypedAtomic)):
            raise self.error('FORG0001', str(err))
        raise self.error('FOCA0002', str(err))


@constructor('integer')
@constructor('nonNegativeInteger')
@constructor('positiveInteger')
@constructor('nonPositiveInteger')
@constructor('negativeInteger')
@constructor('long')
@constructor('int')
@constructor('short')
@constructor('byte')
@constructor('unsignedLong')
@constructor('unsignedInt')
@constructor('unsignedShort')
@constructor('unsignedByte')
def cast(self, value):
    int_subclass = {
        'integer': int,
        'nonNegativeInteger': datatypes.NonNegativeInteger,
        'positiveInteger': datatypes.PositiveInteger,
        'nonPositiveInteger': datatypes.NonPositiveInteger,
        'negativeInteger': datatypes.NegativeInteger,
        'long': datatypes.Long,
        'int': datatypes.Int,
        'short': datatypes.Short,
        'byte': datatypes.Byte,
        'unsignedLong': datatypes.UnsignedLong,
        'unsignedInt': datatypes.UnsignedInt,
        'unsignedShort': datatypes.UnsignedShort,
        'unsignedByte': datatypes.UnsignedByte,
    }
    cls = int_subclass[self.symbol]

    if isinstance(value, (str, bytes, datatypes.UntypedAtomic)):
        try:
            result = self.cast_to_number(value, int)
        except ValueError:
            raise self.error('FORG0001', 'could not convert %r to integer' % value) from None
        except OverflowError as err:
            raise self.error('FORG0001', str(err)) from None
    else:
        try:
            result = int(value)
        except ValueError as err:
            raise self.error('FOCA0002', str(err)) from None
        except OverflowError as err:
            raise self.error('FOCA0002', str(err)) from None

    try:
        return cls(result)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


###
# Constructors for datetime XSD types
@constructor('date')
def cast(self, value):
    cls = datatypes.Date if self.parser.xsd_version == '1.1' else datatypes.Date10
    if isinstance(value, cls):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return cls.fromstring(value.value)
        elif isinstance(value, datatypes.DateTime10):
            return cls(value.year, value.month, value.day, value.tzinfo)
        return cls.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0001', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('gDay')
def cast(self, value):
    if isinstance(value, datatypes.GregorianDay):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.GregorianDay.fromstring(value.value)
        elif isinstance(value, (datatypes.Date10, datatypes.DateTime10)):
            return datatypes.GregorianDay(value.day, value.tzinfo)
        return datatypes.GregorianDay.fromstring(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('gMonth')
def cast(self, value):
    if isinstance(value, datatypes.GregorianMonth):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.GregorianMonth.fromstring(value.value)
        elif isinstance(value, (datatypes.Date10, datatypes.DateTime10)):
            return datatypes.GregorianMonth(value.month, value.tzinfo)
        return datatypes.GregorianMonth.fromstring(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('gMonthDay')
def cast(self, value):
    if isinstance(value, datatypes.GregorianMonthDay):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.GregorianMonthDay.fromstring(value.value)
        elif isinstance(value, (datatypes.Date10, datatypes.DateTime10)):
            return datatypes.GregorianMonthDay(value.month, value.day, value.tzinfo)
        return datatypes.GregorianMonthDay.fromstring(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('gYear')
def cast(self, value):
    cls = datatypes.GregorianYear if self.parser.xsd_version == '1.1' else datatypes.GregorianYear10
    if isinstance(value, cls):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return cls.fromstring(value.value)
        elif isinstance(value, (datatypes.Date10, datatypes.DateTime10)):
            return cls(value.year, value.tzinfo)
        return cls.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0001', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('gYearMonth')
def cast(self, value):
    cls = datatypes.GregorianYearMonth \
        if self.parser.xsd_version == '1.1' else datatypes.GregorianYearMonth10
    if isinstance(value, cls):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return cls.fromstring(value.value)
        elif isinstance(value, (datatypes.Date10, datatypes.DateTime10)):
            return cls(value.year, value.month, value.tzinfo)
        return cls.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0001', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('time')
def cast(self, value):
    if isinstance(value, datatypes.Time):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.Time.fromstring(value.value)
        elif isinstance(value, datatypes.DateTime10):
            return datatypes.Time(value.hour, value.minute, value.second,
                                  value.microsecond, value.tzinfo)
        return datatypes.Time.fromstring(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@method('date')
@method('gDay')
@method('gMonth')
@method('gMonthDay')
@method('gYear')
@method('gYearMonth')
@method('time')
def evaluate(self, context=None):
    arg = self.data_value(self.get_argument(context))
    if arg is None:
        return []

    try:
        return self.cast(arg)
    except ValueError as err:
        raise self.error('FORG0001', str(err)) from None
    except TypeError as err:
        raise self.error('FORG0006', str(err)) from None
    except OverflowError as err:
        raise self.error('FODT0001', str(err)) from None


###
# Constructors for time durations XSD types
@constructor('duration')
def cast(self, value):
    if isinstance(value, datatypes.Duration):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.Duration.fromstring(value.value)
        return datatypes.Duration.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0002', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('yearMonthDuration')
def cast(self, value):
    if isinstance(value, datatypes.YearMonthDuration):
        return value
    elif isinstance(value, datatypes.Duration):
        return datatypes.YearMonthDuration(months=value.months)

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.YearMonthDuration.fromstring(value.value)
        return datatypes.YearMonthDuration.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0002', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('dayTimeDuration')
def cast(self, value):
    if isinstance(value, datatypes.DayTimeDuration):
        return value
    elif isinstance(value, datatypes.Duration):
        return datatypes.DayTimeDuration(seconds=value.seconds)

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return datatypes.DayTimeDuration.fromstring(value.value)
        return datatypes.DayTimeDuration.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0002', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@constructor('dateTimeStamp')
def cast(self, value):
    if isinstance(value, datatypes.DateTimeStamp):
        return value
    elif isinstance(value, datatypes.DateTime10):
        value = str(value)

    try:
        return datatypes.DateTimeStamp.fromstring(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err))


@method('dateTimeStamp')
def evaluate(self, context=None):
    arg = self.data_value(self.get_argument(context))
    if arg is None:
        return []

    try:
        if isinstance(arg, datatypes.UntypedAtomic):
            return self.cast(arg.value)
        return self.cast(str(arg))
    except ValueError as err:
        raise self.error('FOCA0002', str(err)) from None
    except TypeError as err:
        raise self.error('FORG0006', str(err)) from None


###
# Constructors for binary XSD types
@constructor('base64Binary')
def cast(self, value):
    try:
        return datatypes.Base64Binary(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err)) from None
    except TypeError as err:
        if isinstance(value, str):
            raise self.error('FORG0006', str(err)) from None
        raise self.error('XPTY0004', str(err)) from None


@constructor('hexBinary')
def cast(self, value):
    try:
        return datatypes.HexBinary(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err)) from None
    except TypeError as err:
        if isinstance(value, str):
            raise self.error('FORG0006', str(err)) from None
        raise self.error('XPTY0004', str(err)) from None


@method('base64Binary')
@method('hexBinary')
def evaluate(self, context=None):
    arg = self.data_value(self.get_argument(context))
    if arg is None:
        return []

    try:
        return self.cast(arg)
    except ElementPathError as err:
        err.token = self
        raise
    except UnicodeEncodeError as err:
        raise self.error('FORG0001', str(err)) from None


@constructor('NOTATION')
def cast(self, value):
    return value


@method('NOTATION')
def nud(self):
    self.parser.advance('(')
    if self.parser.next_token.symbol == ')':
        raise self.error('XPST0017', 'expected exactly one argument')
    self[0:] = self.parser.expression(5),
    if self.parser.next_token.symbol != ')':
        raise self.error('XPST0017', 'expected exactly one argument')
    self.parser.advance()
    self.value = None
    raise self.error('XPST0017', "no constructor function exists for xs:NOTATION")


###
# Multi role-tokens constructors (function or constructor)
#

# Case 1: In XPath 2.0 the 'boolean' keyword is used both for boolean() function and
# for boolean() constructor.
unregister('boolean')


@constructor('boolean', bp=90, label=('function', 'constructor'))
def cast(self, value):
    try:
        return datatypes.BooleanProxy(value)
    except ValueError as err:
        raise self.error('FORG0001', str(err)) from None
    except TypeError as err:
        if isinstance(value, str):
            raise self.error('FORG0006', str(err)) from None
        raise self.error('XPTY0004', str(err)) from None


@method('boolean')
def nud(self):
    self.parser.advance('(')
    if self.parser.next_token.symbol == ')':
        raise self.wrong_nargs('Too few arguments: expected at least 1 argument')
    self[0:] = self.parser.expression(5),
    if self.parser.next_token.symbol == ',':
        raise self.wrong_nargs('Too many arguments: expected at most 1 argument')
    self.parser.advance(')')
    self.value = None
    return self


@method('boolean')
def evaluate(self, context=None):
    if self.label == 'function':
        return self.boolean_value([x for x in self[0].select(context)])

    # xs:boolean constructor
    arg = self.data_value(self.get_argument(context))
    if arg is None:
        return []

    try:
        return self.cast(arg)
    except ElementPathError as err:
        err.token = self
        raise


###
# Case 2: In XPath 2.0 the 'string' keyword is used both for fn:string() and xs:string().
unregister('string')
register('string', lbp=90, rbp=90, label=('function', 'constructor'),  # pragma: no cover
         pattern=r'\bstring(?=\s*\(|\s*\(\:.*\:\)\()', cast=XPathToken.string_value)


@method('string')
def nud(self):
    try:
        self.parser.advance('(')
        if self.label != 'function' or self.parser.next_token.symbol != ')':
            self[0:] = self.parser.expression(5),
        self.parser.advance(')')
    except ElementPathSyntaxError as err:
        err.code = self.parser.get_qname(XQT_ERRORS_NAMESPACE, 'XPST0017')
        raise

    self.value = None
    return self


@method('string')
def evaluate(self, context=None):
    if self.label == 'function':
        if not self:
            if context is None:
                raise self.missing_context()
            return self.string_value(context.item)
        return self.string_value(self.get_argument(context))
    else:
        item = self.get_argument(context)
        return [] if item is None else self.string_value(item)


# Case 3 and 4: In XPath 2.0 the XSD 'QName' and 'dateTime' types have special
# constructor functions so the 'QName' keyword is used both for fn:QName() and
# xs:QName(), the same for 'dateTime' keyword.
#
# In those cases the label at parse time is set by the nud method, in dependence
# of the number of args.
#
@constructor('QName', bp=90, label=('function', 'constructor'))
def cast(self, value):
    if isinstance(value, datatypes.QName):
        return value
    elif isinstance(value, datatypes.UntypedAtomic):
        value = value.value
    elif not isinstance(value, str):
        raise self.error('XPTY0004', 'the argument has an invalid type %r' % type(value))

    try:
        if ':' not in value:
            return datatypes.QName(self.parser.namespaces.get('', ''), value)
        pfx, _ = value.strip().split(':')
        return datatypes.QName(self.parser.namespaces[pfx], value)
    except ValueError:
        raise self.error('FORG0001', 'invalid value {!r} for argument'.format(value.strip()))
    except KeyError as err:
        raise self.error('FONS0004', 'no namespace found for prefix {}'.format(err))


@constructor('dateTime', bp=90, label=('function', 'constructor'))
def cast(self, value):
    cls = datatypes.DateTime if self.parser.xsd_version == '1.1' else datatypes.DateTime10
    if isinstance(value, cls):
        return value

    try:
        if isinstance(value, datatypes.UntypedAtomic):
            return cls.fromstring(value.value)
        elif isinstance(value, datatypes.Date10):
            return cls(value.year, value.month, value.day, tzinfo=value.tzinfo)
        return cls.fromstring(value)
    except OverflowError as err:
        raise self.error('FODT0001', str(err)) from None
    except ValueError as err:
        raise self.error('FORG0001', str(err)) from None


@method('QName')
@method('dateTime')
def nud(self):
    try:
        self.parser.advance('(')
        self[0:] = self.parser.expression(5),
        if self.parser.next_token.symbol == ',':
            if self.label != 'function':
                raise self.error('XPST0017', 'unexpected 2nd argument')
            self.label = 'function'
            self.parser.advance(',')
            self[1:] = self.parser.expression(5),
        elif self.label != 'constructor' or self.namespace != XSD_NAMESPACE:
            raise self.error('XPST0017', '2nd argument missing')
        else:
            self.label = 'constructor'
        self.parser.advance(')')
    except SyntaxError:
        raise self.error('XPST0017') from None
    self.value = None
    return self


@method('QName')
def evaluate(self, context=None):
    if self.label == 'constructor':
        arg = self.data_value(self.get_argument(context))
        return [] if arg is None else self.cast(arg)
    else:
        uri = self.get_argument(context)
        qname = self.get_argument(context, index=1)
        try:
            return datatypes.QName(uri, qname)
        except TypeError as err:
            raise self.error('XPTY0004', str(err))
        except ValueError as err:
            if isinstance(context, XPathSchemaContext):
                return datatypes.ATOMIC_VALUES['QName']
            raise self.error('FOCA0002', str(err))


@method('dateTime')
def evaluate(self, context=None):
    if self.label == 'constructor':
        arg = self.data_value(self.get_argument(context))
        if arg is None:
            return []

        try:
            return self.cast(arg)
        except ValueError as err:
            raise self.error('FORG0001', str(err)) from None
        except TypeError as err:
            raise self.error('FORG0006', str(err)) from None
    else:
        dt = self.get_argument(context, cls=datatypes.Date10)
        tm = self.get_argument(context, 1, cls=datatypes.Time)
        if dt is None or tm is None:
            return []
        elif dt.tzinfo == tm.tzinfo or tm.tzinfo is None:
            tzinfo = dt.tzinfo
        elif dt.tzinfo is None:
            tzinfo = tm.tzinfo
        else:
            raise self.error('FORG0008')

        if self.parser.xsd_version == '1.1':
            return datatypes.DateTime(dt.year, dt.month, dt.day, tm.hour, tm.minute,
                                      tm.second, tm.microsecond, tzinfo)
        return datatypes.DateTime10(dt.year, dt.month, dt.day, tm.hour, tm.minute,
                                    tm.second, tm.microsecond, tzinfo)


@constructor('untypedAtomic')
def cast(self, value):
    return datatypes.UntypedAtomic(value)


@method('untypedAtomic')
def evaluate(self, context=None):
    arg = self.data_value(self.get_argument(context))
    if arg is None:
        return []
    elif isinstance(arg, datatypes.UntypedAtomic):
        return arg
    else:
        return self.cast(arg)


XPath2Parser.build()  # XPath 2.0 definition complete, can build the parser class.
