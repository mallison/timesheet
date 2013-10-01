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
    
Get a report like this:

    Mon Sep 30, 2013
    bb: eu                         2h 23m          ##################################################
    code review: country/lang tagg 2h 10m          #############################################
                                   1h 13m          #########################
    500: counselling               54m             ##################
    dev ops                        30m             ##########
    stand up                       16m             #####
    OVERALL                        7h 26m

See your commit activity per task with the ``--commit`` switch.

    Mon Sep 30, 2013
    bb: eu                         2h 23m          ##################################################
        1136 commit: fixes to chatrooms views
        1136 commit: fixes to chatroom module
        1103 commit: Bring back supervision room view
        1103 commit: Fix main chatroom view
        1332 WIP on minor-lang-chat: ca417a9 Add links to other chatrooms from chat module

    code review: country/lang tagg 2h 10m          #############################################

                                   1h 13m          #########################

    500: counselling               54m             ##################
        0918 branch: Created from master

    dev ops                        30m             ##########

    stand up                       16m             #####
        1253 commit: Add links to other chatrooms from chat module

    OVERALL             	       7h 26m

See also the ``--stand-up`` and ``--eom`` options.

