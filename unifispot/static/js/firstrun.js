
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
          
        var firstrun_steps = {
                bodyTag: "fieldset",
                onStepChanging: function (event, currentIndex, newIndex)
                {
                    // Always allow going backward even if the current step contains invalid fields!
                    if (currentIndex > newIndex)
                    {
                        return true;
                    }

                    // Forbid suppressing "Warning" step if the user is to young
                    if (newIndex === 3 && Number($("#age").val()) < 18)
                    {
                        return false;
                    }

                    var form = $(this);

                    // Clean up if user went backward before
                    if (currentIndex < newIndex)
                    {
                        // To remove error styles
                        $(".body:eq(" + newIndex + ") label.error", form).remove();
                        $(".body:eq(" + newIndex + ") .error", form).removeClass("error");
                    }

                    // Disable validation on fields that are disabled or hidden.
                    form.validate().settings.ignore = ":disabled,:hidden";

                    // Start validation; Prevent going forward if false
                    return form.valid();
                },
                onStepChanged: function (event, currentIndex, priorIndex)
                {
                    // Suppress (skip) "Warning" step if the user is old enough.
                    if (currentIndex === 2 && Number($("#age").val()) >= 18)
                    {
                        $(this).steps("next");
                    }

                    // Suppress (skip) "Warning" step if the user is old enough and wants to the previous step.
                    if (currentIndex === 2 && priorIndex === 3)
                    {
                        $(this).steps("previous");
                    }
                },
                onFinishing: function (event, currentIndex)
                {
                    var form = $(this);

                    // Disable validation on fields that are disabled.
                    // At this point it's recommended to do an overall check (mean ignoring only disabled fields)
                    form.validate().settings.ignore = ":disabled";

                    // Start validation; Prevent form submission if false
                    return form.valid();
                },
                onCanceled: function (event)
                {



                },                
                onFinished: function (event, currentIndex)
                {
                    var form = $(this);

                    // Submit form input
                    url = '/admin/settings/api/'
                    $.ajaxSetup({
                        type: 'POST',
                        timeout: 30000,
                        error: function(xhr) {
                                $.unblockUI("#firstrun-form");
                                toastr.options= toastr_options;
                                var $toast = toastr['error']("ERROR", "Network timeout!!,Please try again later");
                             }
                     });
                    //block UI while form is processed
                    $.blockUI({target: "#firstrun-form"});
                    //$('#'+modal).modal('hide');
                    $.post(url, $( "#firstrun-form" ).serialize(),function(data) {

                            $.unblockUI("#firstrun-form");
                            if(data.status){
                                toastr.options= toastr_options;
                                var $toast = toastr['success']("Success", data.msg);
                                location.reload();
                            }
                            else{
                                toastr.options= toastr_options;
                                var $toast = toastr['error']("ERROR", data.msg);
  
                            }
                        },
                        'json'// I expect a JSON response
                    );
                }
            }
        var firstrun_validate ={
                        errorPlacement: function (error, element)
                        {
                            element.before(error);
                        },
                        rules: {
                            accept_tos: {
                                required:true,
                            },   
                              

                        },
                        messages: {
                            accept_tos: {
                              required: "Please read and accept Terms"
                            },         
                            
                      }
                    }

        $(document).ready(function(){      


            $("#firstrun-form").steps(firstrun_steps).validate(firstrun_validate);
       });