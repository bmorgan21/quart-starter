from typing import Any

from .pagination import PageInfo


class Query:
    filters: Any
    sorts: Any
    resolves: Any
    page_info: PageInfo

    async def queryset(self, model):
        queryset = model.all()
        if self.filters:
            queryset = queryset.filter(**{x.field: x.value for x in self.filters})

        if self.sorts:
            queryset = queryset.order_by(*self.sorts)

        if self.resolves:
            queryset = queryset.prefetch_related(*self.resolves)

        return await self.page_info.paginate(queryset)
