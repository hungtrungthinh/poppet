var AnalyticsDashboard = function(api_url) {

    function cb(start, end) {
        $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
    }
    cb(moment().subtract(29, 'days'), moment());

    $('#reportrange').daterangepicker({
        ranges: {
           'Today': [moment(), moment()],
           'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Last 7 Days': [moment().subtract(6, 'days'), moment()],
           'Last 30 Days': [moment().subtract(29, 'days'), moment()],
           'This Month': [moment().startOf('month'), moment().endOf('month')],
           'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
    }, cb);

    $('#reportrange').on('apply.daterangepicker', function(ev, picker) {
        start = picker.startDate.format('DD-MM-YYYY');
        end = picker.endDate.format('DD-MM-YYYY');
        update_dashboard(start,end);
    });

    var start_d = moment().subtract(29, 'days').format('DD-MM-YYYY');
    var end_d = moment().format('DD-MM-YYYY');
    update_dashboard(start_d,end_d);

    function update_dashboard(start,end){
        //start = picker.startDate.format('DD-MM-YYYY');
        //end = picker.endDate.format('DD-MM-YYYY');
        url = api_url+'?start='+start+'&end='+end
        
        $.blockUI();
        $.ajaxSetup({
            type: 'GET',
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI();
                    toastr.options= toastr_options;
                    var $toast = toastr['error']("ERROR", "Network timeout!!,Please try again later");
                 }
         });        
        $.get(url,function(data) {
                if(data.status){
                    $.unblockUI();
                //-------------------------flot chart start----------------------------------
                   var dataset = [
                                {
                                    label: "Total Logins",
                                    data: data.logins,
                                    color: "#1ab394",
                                    bars: {
                                        show: true,
                                        align: "center",
                                        barWidth: 24 * 60 * 60 * 600,
                                        lineWidth:0
                                    }

                                }, {
                                    label: "New Guests",
                                    data: data.newlogins,
                                    color: "#1C84C6",
                                    lines: {
                                        lineWidth:1,
                                            show: true,
                                            fill: true,
                                        fillColor: {
                                            colors: [{
                                                opacity: 0.2
                                            }, {
                                                opacity: 0.4
                                            }]
                                        }
                                    },
                                    splines: {
                                        show: false,
                                        tension: 0.6,
                                        lineWidth: 1,
                                        fill: 0.1
                                    },
                                }
                            ];
                    var options = {
                        xaxis: {
                            mode: "time",
                            tickSize: [3, "day"],
                            tickLength: 0,
                            axisLabel: "Date",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Arial',
                            axisLabelPadding: 10,
                            color: "#d5d5d5"
                        },
                        yaxes: [{
                            position: "left",
                            max: data.maxlogin,
                            color: "#d5d5d5",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Arial',
                            axisLabelPadding: 3
                        }
                        ],
                        legend: {
                            noColumns: 1,
                            labelBoxBorderColor: "#000000",
                            position: "nw"
                        },
                        grid: {
                            hoverable: false,
                            borderWidth: 0
                        }
                    };

                    var previousPoint = null, previousLabel = null;
                    $.plot($("#flot-dashboard-chart"), dataset, options); 

                //-------------------------flot chart end---------------------------------- 
                
                //-------------------------widgets start-----------------------------------  
                $('#total_visits').text(data.total_visits);
                $('#total_logins').text(data.total_logins);
                $('#total_likes').text(data.total_likes);
                $('#total_checkins').text(data.total_checkins);
                //-------------------------widgets end-----------------------------------  

                //---------------------------Pie chart start-----------------------------
                var doughnutData = [
                    {
                        value: data.total_emails,
                        color: "#a3e1d4",
                        highlight: "#1ab394",
                        label: "Email"
                    },
                    {
                        value: data.total_fbs,
                        color: "#dedede",
                        highlight: "#1ab394",
                        label: "Facebook"
                    },
                    {
                        value: data.total_vouchers,
                        color: "#b5b8cf",
                        highlight: "#1ab394",
                        label: "Voucher"
                    },
                    {
                        value: data.total_phones,
                        color: "#2f4050",
                        highlight: "#676a6c",
                        label: "Phones"
                    }                    
                ];

                var doughnutOptions = {
                    segmentShowStroke: true,
                    segmentStrokeColor: "#fff",
                    segmentStrokeWidth: 2,
                    percentageInnerCutout: 45, // This is 0 for Pie charts
                    animationSteps: 100,
                    animationEasing: "easeOutBounce",
                    animateRotate: true,
                    animateScale: false,
                    responsive: true,
                };


                var ctx = document.getElementById("doughnutChart").getContext("2d");
                var myNewChart = new Chart(ctx).Doughnut(doughnutData, doughnutOptions);


                //---------------------------Pie chart end-----------------------------

                //--------------------------Social chart start-------------------------

                   var dataset = [
                                {
                                    label: "New Likes",
                                    data: data.likes,
                                    color: "#23c6c8",


                                }, {
                                    label: "New Checkins",
                                    data: data.checkins,
                                    color: "#f8ac59",

                                }
                            ];
                    var options = {
                        xaxis: {
                            mode: "time",
                            tickSize: [3, "day"],
                            tickLength: 0,
                            axisLabel: "Date",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Arial',
                            axisLabelPadding: 10,
                            color: "#d5d5d5"
                        },
                        yaxes: [{
                            position: "left",
                            max: data.maxsocial,
                            color: "#d5d5d5",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Arial',
                            axisLabelPadding: 3
                        }
                        ],
                        legend: {
                            noColumns: 1,
                            labelBoxBorderColor: "#000000",
                            position: "nw"
                        },
                        grid: {
                            hoverable: false,
                            borderWidth: 0
                        }
                    };

                    var previousPoint = null, previousLabel = null;
                    $.plot($("#flot-social-chart"), dataset, options); 
                    //--------------------------Social chart end-------------------------
                }
                else{
                    $.unblockUI();
                    toastr.options= toastr_options;
                    var $toast = toastr['error']("ERROR", data.msg);
                }
            },
            'json'// I expect a JSON response
        );
         
    }




}