select ud.user_id, max(ud.jpy_amount), avg(ud.jpy_amount)
from (select ud.user_id as user_id, ud.jpy_amount as jpy_amount, row_number() over (partition by user_id order by id desc) as seqnum
      from session ud
      where scenario = 'Jun_Aug_2016_without_commission'
      and   is_complete = true
     ) ud
where seqnum <= 5
group by ud.user_id;