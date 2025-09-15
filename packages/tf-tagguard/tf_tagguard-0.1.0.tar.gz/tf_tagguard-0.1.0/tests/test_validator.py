import pytest
from tf_tagguard.validator import TagValidator
from tf_tagguard.exceptions import TagValidationError

def test_missing_tag():
    tf_plan = {"resource_changes": [{"address": "aws_s3_bucket.test", "change": {"after": {"tags": {}}}}]}
    validator = TagValidator(required_tags=["Name"])
    with pytest.raises(TagValidationError):
        validator.validate(tf_plan)

def test_valid_tag():
    tf_plan = {"resource_changes": [{"address": "aws_s3_bucket.test", "change": {"after": {"tags": {"Name":"bucket"}}}}]}
    validator = TagValidator(required_tags=["Name"])
    assert validator.validate(tf_plan)
