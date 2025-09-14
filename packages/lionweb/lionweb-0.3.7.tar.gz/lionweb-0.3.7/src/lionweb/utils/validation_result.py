from typing import Set

from lionweb.model import ClassifierInstance
from lionweb.utils.issue import Issue
from lionweb.utils.issue_severity import IssueSeverity


class ValidationResult:
    def __init__(self):
        self.issues: Set[Issue] = set()

    def get_issues(self) -> Set[Issue]:
        return self.issues

    def is_successful(self) -> bool:
        return not self.has_errors()

    def has_errors(self) -> bool:
        return any(issue.is_error() for issue in self.issues)

    def add_error(
        self, message: str, subject: ClassifierInstance
    ) -> "ValidationResult":
        self.issues.add(Issue(IssueSeverity.ERROR, message, subject))
        return self

    def add_error_if(
        self, check: bool, message: str, subject: ClassifierInstance
    ) -> "ValidationResult":
        if check:
            self.issues.add(Issue(IssueSeverity.ERROR, message, subject))
        return self

    def __str__(self):
        return f"ValidationResult({', '.join(str(issue) for issue in self.issues)})"

    def __bool__(self) -> bool:
        return not self.has_errors()
