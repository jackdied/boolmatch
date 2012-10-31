boolmatch
=========

Compare text to a boolean expression of terms.  It was built to replace an existing one created with pyparsing.  That one tended to blow its stack and it didn't like unicode much either.

ANDs have a higher order of precedence than ORs.  Words are implicitly AND'd if there is no operator between them.

    >>> find = u'((trends OR predictions OR forecast)AND technology) OR ("cloud computing" AND security)'
    >>> text = urlopen('http://slashot.org/')
    >>> if boolmatch.matches(find, text):
    ...
    >>>     print "it matches!"
    >>>
    >>> tree = boolmatch.make_parse_tree(find)
    >>> tree
    <AND [<OR [<AND [<Token u'cloud computing' (0, 57)>, <Token u'security' (0, 78)>] ?>, <AND [<OR [<Token u'forecast' (0, 27)>, <Token u'predictions' (0, 12)>, <Token u'trends' (0, 2)>] ?>, <Token u'technology' (0, 40)>] ?>] ?>] ?>
    >>> tree.pretty()
    u"AND ((u'cloud computing' AND security) OR ((forecast OR predictions OR trends) AND technology))"
    >>>
    >>> boolmatch.pprint_tree(tree)
    ? AND
       ? OR
         ? AND
           ? "cloud computing"
           ? security
         ? AND
           ? OR
             ? forecast
             ? predictions
             ? trends
           ? technology
    >>> tree.match('hello world')
    >>> boolmatch.pprint_tree(tree)
    F AND
      F OR
        F AND
          F "cloud computing"
          ? security
        F AND
          F OR
            F forecast
            F predictions
            F trends
          ? technology
