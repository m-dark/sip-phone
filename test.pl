#!/usr/bin/perl -w

use strict;
use warnings;
use Time::HiRes qw(time);
use POSIX qw(strftime);
use Time::Local;

my $date_2 = 11110;
my $minets = 0;
my $i = 0;
while (1){
        my $t = time;
        my $date_ear = strftime "%Y-%m-%d %H:%M:", localtime($t);
        my $minets_new = strftime "%M", localtime($t);
        if (($minets < $minets_new) || ($minets > $minets_new)){
                print "------------------------------------- прошло $i минут\n";
                $minets = $minets_new;
                $i ++;
        }
        my $date = strftime "%S", localtime($t);
        $date .= sprintf "%03d", ($t-int($t))*1000;
        my $rez = $date - $date_2;
        if (($rez > 22) && ($date_2 != 11110)){
                if ($rez > 30){
                        print "$date_ear$date_2\t$rez\t!!!\n";
                }else{
#                        print "$date_ear$date_2\t$rez\n";
                }
        }
        $date_2 = $date;
        Time::HiRes::sleep(0.02);
#print "$date\n";
}