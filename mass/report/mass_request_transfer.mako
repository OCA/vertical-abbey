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

% for trf in objects:

<h1>${_("Mass Transfer")}</h1>

<h2>${_("Transfer Date:")} ${trf.transfer_date}</h2>

<h3>${_("Amount Total:")} ${formatLang(trf.amount_total)}</h3>
<h3>${_("Total Number of Masses:")} ${formatLang(trf.mass_total)}</h3>

    <table>
    <tr>
        <th>${_("Donor")}</th>
        <th>${_("Donation Date")}</th>
        <th>${_("Mass Request Code")}</th>
        <th>${_("Quantity")}</th>
        <th>${_("Offering")}</th>
        <th>${_("Intention")}</th>
    </tr>

% for req in trf.mass_request_ids:

    <tr>
        <td>${req.donor_id and req.donor_id.name or ''}</td>
        <td>${req.donation_date and formatLang(req.donation_date, date=True) or ''}</td>
        <td>${req.type_id.code}</td>
        <td>${req.quantity}</td>
        <td>${req.offering}</td>
        <td>${req.intention or ''}</td>
    </tr>
%endfor

    </table>
%endfor
</body>
</html>


