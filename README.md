timesheet
=========

Create task/time reports from a simple timesheet text file.

Track your time in a file like this:

    Monday                                                                                                                                                                                                  
    0917 500: counselling                                                                                                                                                                                   
    stick twist permission in both counsellor groups. sigh                                                                                                                                                  
                                                                                                                                                                                                            
    1011 dev ops                                                                                                                                                                                            
                                                                                                                                                                                                            
    1041 bb: eu: minor lang chat                                                                                                                                                                            
                                                                                                                                                                                                            
    1245 stand up                                                                                                                                                                                           
                                                                                                                                                                                                            
    1301 lunch                                                                                                                                                                                              
                                                                                                                                                                                                            
    1332 bb: eu: minor lang chat

    1351 code review: country/lang tagging

    1601

    1714

Run the timesheet script:

    $ python /path/to/timesheet/package /path/to/timesheet/text/file [/another/timesheet/file ....]
    
Get this report:

    Tue 19 Jan......................................................................  1d     26m
      bb                                                                                        
        eu                                                                                      
          minor lang chat...........................................................      2h 23m
      code review                                                                               
        country/lang tagging........................................................      2h 10m
      misc..........................................................................      1h 13m
      500                                                                                       
        counselling.................................................................         54m
      dev ops.......................................................................         30m
      stand up......................................................................         16m
