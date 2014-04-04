<html>
<style>
    .label { display:inline-block; width:100%; height:100%; color:#000; font-family:"times new roman", times, serif;}
    .label table {  width:100%; height:100%;}
    .label_top{  display:block; height:30px; padding-top:0px;  border-bottom: 2px solid #000;}
    .label_top table { font-size:10px; width:100%; border:0px; margin:0px; padding:0px;  }
    .label_top table td { padding:2px; text-align:left; width:28%;}
</style>
<body>

<% setLang(user.lang) %>

<h1>${_("Guest List")}</h1>

<% dico = report_by_refectory(objects) %>

% for date in sorted(dico):

<h2>${_("Date:")} ${formatLang(date, date=True)}</h2>

<div class="label">
    % for (refectory, dicol2) in dico[date].iteritems():
        <h3>${refectory.name}</h3>
    <table>
    <tr>
        <th>${_("Stay Nr")}</th>
        <th>${_("Arrival Date")}</th>
        <th>${_("Departure Date")}</th>
        <th>${_("Guest")}</th>
        <th>${_("Room")}</th>
        <th>${_("Lunch")}</th>
        <th>${_("Dinner")}</th>
        <th>${_("Night")}</th>
    </tr>


    %for line in dicol2['lines']:
    <tr>
        <td>${line.stay_id and line.stay_id.name or ''}</td>
        <td>${line.stay_id and line.stay_id.arrival_date or ''} ${line.stay_id and line.stay_id.arrival_time or ''}</td>
        <td>${line.stay_id and line.stay_id.departure_date or ''} ${line.stay_id and line.stay_id.departure_time or ''}</td>
        <td>${line.partner_name or ''}</td>
        <td>${line.room_id and line.room_id.code or ''}</td>
        <td>${line.lunch_qty}</td>
        <td>${line.dinner_qty}</td>
        <td>${line.bed_night_qty}</td>
    </tr>
    %endfor
    <tr>
        <td></td>
        <td></td>
        <td></td>
        <td colspan="2"><b>${_('Sub-totals :')}</b></td>
        <td>${dicol2['lunch_subtotal']}</td>
        <td>${dicol2['dinner_subtotal']}</td>
        <td>${dicol2['bed_night_subtotal']}</td>
    </tr>
    </table>
    %endfor
%endfor
</div>
</body>
</html>


