from dateutil.relativedelta import relativedelta, weekday
from rest_framework.utils.urls import replace_query_param

from mymoney.core.utils.dates import (
    GRANULARITY_MONTH, GRANULARITY_WEEK, get_weekday,
)


class InvalidDateRanges(Exception):
    pass


class UnknownGranularity(Exception):
    pass


class EmptyPage(Exception):
    pass


class DatePaginator(object):

    page_query_param = 'date'

    def __init__(self, date_min, date_max, granularity):

        if date_min >= date_max:
            raise InvalidDateRanges("Date min could not be greater or equals "
                                    "than date max.")
        self.date_min = date_min
        self.date_max = date_max

        if granularity not in (GRANULARITY_MONTH, GRANULARITY_WEEK):
            raise UnknownGranularity('Unknow granularity: %s' % granularity)
        self.granularity = granularity

        self.week_day = get_weekday()

    def page(self, base_date):

        if not (self.date_min <= base_date <= self.date_max):
            raise EmptyPage("Base date is out of ranges.")

        if self.granularity == GRANULARITY_MONTH:
            return MonthlyDatePage(base_date, self.date_min, self.date_max,
                                   self)

        elif self.granularity == GRANULARITY_WEEK:  # pragma: no branch
            return WeeklyDatePage(base_date, self.date_min, self.date_max,
                                  self, week_day=self.week_day)

    def get_links(self, base_date, request):
        page = self.page(base_date)
        return {
            'previous': self.get_previous_link(page, request),
            'next': self.get_next_link(page, request),
        }

    def get_previous_link(self, page, request):
        if not page.has_previous():
            return None
        url = request.build_absolute_uri()
        page_date = page.previous_date()
        return replace_query_param(url, self.page_query_param, page_date)

    def get_next_link(self, page, request):
        if not page.has_next():
            return None
        url = request.build_absolute_uri()
        page_date = page.next_date()
        return replace_query_param(url, self.page_query_param, page_date)


class BaseDatePage(object):

    def __init__(self, date, date_min, date_max, paginator):
        self.date = date
        self.date_min = date_min
        self.date_max = date_max
        self.paginator = paginator

    def has_next(self):
        return self.next_date() <= self.date_max

    def has_previous(self):
        return self.previous_date() >= self.date_min

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_date(self):
        raise NotImplementedError

    def previous_date(self):
        raise NotImplementedError


class MonthlyDatePage(BaseDatePage):

    def next_date(self):
        return self.date + relativedelta(months=1, day=1)

    def previous_date(self):
        return self.date + relativedelta(months=-1, day=1)


class WeeklyDatePage(BaseDatePage):

    def __init__(self, *args, **kwargs):
        self.week_day = kwargs.pop('week_day', 0)
        super(WeeklyDatePage, self).__init__(*args, **kwargs)

    def next_date(self):
        return self.date + relativedelta(
            weekday=weekday(self.week_day, n=-1),
            weeks=1,
        )

    def previous_date(self):
        return self.date + relativedelta(
            weekday=weekday(self.week_day, n=-1),
            weeks=-1,
        )
