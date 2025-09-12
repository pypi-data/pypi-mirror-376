"""A django field definition for Postgres hierarchical ltree field.

Source: https://github.com/whitglint/ltreefield
license: MIT, https://github.com/whitglint/ltreefield/blob/master/LICENSE
"""

from django.db import models
from django.db.models import Lookup


class LtreeField(models.CharField):
    description = "SQLite alternative to ltree (up to %(max_length)s)"

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 256
        super().__init__(*args, **kwargs)

    # def db_type(self, connection):
    #    return "ltree"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        return name, path, args, kwargs


class AncestorOrEqual(Lookup):
    lookup_name = "aore"

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        if len(rhs_params) > 1:
            raise ValueError("This alternative for LTree is not implemented")
        elif len(rhs_params[0]) > 2:
            return (
                '%s like %s or %s like %s or %s like ""  '
                % (lhs, rhs, lhs, rhs_params[0][:-2], lhs),
                params,
            )
        else:
            return '%s like %s or %s like "" ' % (lhs, rhs, lhs), params


LtreeField.register_lookup(AncestorOrEqual)


class DescendantOrEqual(Lookup):
    lookup_name = "dore"

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        if len(params) > 1:
            raise ValueError("This alternative for LTree is not implemented")
        else:
            params = [params[0] + "%"]
            return "%s like %s" % (lhs, rhs), params


LtreeField.register_lookup(DescendantOrEqual)


class Match(Lookup):
    lookup_name = "match"

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return "%s like %s" % (lhs, rhs), params


LtreeField.register_lookup(Match)
