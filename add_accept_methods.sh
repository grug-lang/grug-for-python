#!/bin/bash
CLASSES=(
"TrueExpr"
"FalseExpr"
"StringExpr"
"ResourceExpr"
"EntityExpr"
"IdentifierExpr"
"NumberExpr"
"UnaryExpr"
"BinaryExpr"
"LogicalExpr"
"CallExpr"
"ParenthesizedExpr"
"VariableStatement"
"CallStatement"
"IfStatement"
"ReturnStatement"
"WhileStatement"
"BreakStatement"
"ContinueStatement"
"EmptyLineStatement"
"CommentStatement"
"OnFn"
"HelperFn"
)

for CLASS in "${CLASSES[@]}"
do
  sed -i "/@dataclass\\nclass ${CLASS}/a\\    def accept(self, visitor):\\n        return visitor.visit(self)\\n" src/grug/parser.py
done
