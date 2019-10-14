#!/usr/bin/perl -w

use 5.010;
use strict;
use warnings;
use POSIX qw(strftime);
use locale;
use Time::Local;
use encoding 'utf-8';
use DBI;
use File::Copy;

my $dir = '/opt/asterisk/script';
my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		# пароль /etc/freepbx.conf
my $db = '';		#"asterisk"; # имя базы данных.
my $user_name = '';	#
my $user_email = '';	#
my $domen = '';		#Домен
open (my $freepbx_pass, '<:encoding(UTF-8)', "$dir/freepbx.pass") || die "Error opening file: freepbx.pass $!";
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
			}when('db'){
				$db = $array_freepbx_pass[1];
			}when('domen'){
				$domen = $array_freepbx_pass[1];
			}when('user_name'){
				$user_name = $array_freepbx_pass[1];
			}when('user_email'){
				$user_email = $array_freepbx_pass[1];
			}default{
#				print "Лишняя строка в freepbx.pass\n";
				next;
			}
		}
	}
close($freepbx_pass);
my $number = $ARGV[0];

open (my $file, '<:encoding(UTF-8)', "$dir/number-fax.conf") || die "Error opening file: number-fax.conf $!";
	while (defined(my $lime_number_fax = <$file>)){
		chomp ($lime_number_fax);
		if ($lime_number_fax =~ /$number$/){
			my @array_number_fax = split (/\t/,$lime_number_fax,-1);
			$user_name = $array_number_fax[0];
			last;
		}
	}
close ($file);

my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
my $sth = $dbasterisk->prepare("SELECT email FROM userman_users WHERE username=\'$user_name\';");
$sth->execute; # исполняем запрос
while (my $ref = $sth->fetchrow_arrayref) {
	if (($$ref[0] ne '') && ($$ref[0] =~ /\@$domen$/)){
		$user_email = $$ref[0];
	}else{
		#Если поле email пустое или не содержит @$domen, то почту отправляем на $user_email
	}
#	print "$user_email\n"; # печатаем результат
}
my $rc = $sth->finish;
$rc = $dbasterisk->disconnect;  # закрываем соединение
print "$user_email";
