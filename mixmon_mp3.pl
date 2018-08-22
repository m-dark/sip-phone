#!/usr/bin/perl -w
# Скрипт конвертирует wav файлы в mp3 и правит название файла в базе asteriskcdrdb
# Проверить колличество wav файлов в базе asteriskcdrdb можно запросом:
# select recordingfile from cdr Where cdr.recordingfile LIKE "%wav";
# Скрипт написал Крук Иван Александрович kruk.ivan@itmh.ru

use 5.010;
use strict;
use warnings;
use POSIX qw(strftime);
use locale;
use DBI;
use Time::Local;
use encoding 'utf-8';
#use Date::Dumper qw(Dumper);
#fwconsole userman --syncall --force

my $dir_conf = '/etc/asterisk/script';
my $file_pass = 'freepbx.pass';
my $dir_monitor = '/var/spool/asterisk/monitor';
my $wav_file = $ARGV[0];

my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		#пароль /etc/freepbx.conf
my $cdrdb = '';		#asteriskcdrdb # имя базы данных.
my $cdrtable = '';
open (my $freepbx_pass, '<:encoding(UTF-8)', "$dir_conf/freepbx.pass") || die "Error opening file: freepbx.pass $!";
	while (defined(my $line_freepbx_pass = <$freepbx_pass>)){
		chomp ($line_freepbx_pass);
		if ($line_freepbx_pass =~ /^\#/){
			next;
		}
		my @array_freepbx_pass = split (/ = /,$line_freepbx_pass,-1);
		given($array_freepbx_pass[0]){
			when('host'){
				$host = $array_freepbx_pass[1];
			}when('port'){
				$port = $array_freepbx_pass[1];
			}when('user'){
				$user = $array_freepbx_pass[1];
			}when('pass'){
				$pass = $array_freepbx_pass[1];
			}when('cdrdb'){
				$cdrdb = $array_freepbx_pass[1];
			}when('cdrtable'){
				$cdrtable = $array_freepbx_pass[1];
			}default{
				next;
			}
		}
	}
close($freepbx_pass);

if (defined ($wav_file)){
}else{
	$wav_file = '*.wav';
}
my $dbasteriskcdr = DBI->connect("DBI:mysql:$cdrdb:$host:$port",$user,$pass,{ mysql_enable_utf8 => 1 });

for my $dir_and_file_wav (`find /var/spool/asterisk/monitor -type f -name "$wav_file"`){
#for my $dir_and_file_wav (`find /etc/asterisk/script/06 -type f -name "$wav_file"`){
	chomp($dir_and_file_wav);
	my $file_wav = `basename "$dir_and_file_wav" .wav`;
	chomp($file_wav);
	my $dir = `dirname "$dir_and_file_wav"`;
	chomp($dir);
	`lame -h -b 192 "$dir_and_file_wav" "$dir/$file_wav.mp3"`;
	`rm -f "$dir/$file_wav.wav"`;
	my $sth_ad = $dbasteriskcdr->do("UPDATE $cdrtable SET recordingfile = '$file_wav.mp3' WHERE $cdrtable.recordingfile = '$file_wav.wav';") || &die_clean("$dbasteriskcdr->errstr. $!\n" );
}
my $rc = $dbasteriskcdr->disconnect;  # закрываем соединение

sub die_clean{
my @error = @_;
open (my $error_db, '>>:encoding(UTF-8)', "$dir_conf/error_db.log") || die "Error opening file: error_db.log $!";
	print $error_db "@error\n";
close ($error_db);
}