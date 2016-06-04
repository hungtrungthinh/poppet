$(document).ready(function() {
    var toastr_options = {
        "closeButton": true,
        "debug": false,
        "positionClass": "toast-top-right",
        "onclick": null,
        "showDuration": "1000",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
        };    
    $('.close-notification').click(function(e) {
        //setup timeout for Post and enable error display
        e.preventDefault();        
        id = $(this).attr('id');
        $.ajaxSetup({
            type: 'POST',
            timeout: 30000,
            error: function(xhr) {
                    $.unblockUI();
                    toastr.options= toastr_options;
                    var $toast = toastr['error']("ERROR", "Network timeout!!,Please try again later");
                 }
         });
        //block UI while form is processed
        $.blockUI({boxed: true});
        $.post(url,function(data) {
                $.unblockUI();
                if(data.status){
                    $('#notification-'+id).hide();
                }
                else{
                    toastr.options= toastr_options;
                    var $toast = toastr['error']("ERROR", data.msg);
                }
            },
            'json'// I expect a JSON response
        );
        return false;
    });

        
});