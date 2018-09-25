#!/usr/bin/perl -w
#Для запуска данного скрипта необходимо расшарить права chmod 777 pdf_to_tiff.pl
use 5.010;
use strict;
use warnings;
use POSIX qw(strftime);
use locale;
use Time::Local;
use encoding 'utf-8';
use DBI;

use File::Copy;

my $dir = '/etc/asterisk/script';
my $dir_tiff = '/mnt/fax_out';
my $ext = '';
my $num = 0;
my $number_fax_start = 5000;
my %hash_number_fax = ();
my $file_name = $ARGV[0];			#Путь до файла /var/spool/cups-pdf/, менять можно в: /etc/cups/cups_pdf.conf
my $user_name = $ARGV[1];
my $i = 0;
my $date_time_file = strftime "%Y-%m-%d_%H%M%S", localtime(time);
my $comment = '';

# Устанавливаем путь по умолчанию
$ENV{PATH} = '/bin:/usr/bin:/sbin:/usr/sbin';
# Делаем корень текущим каталогом
#chdir '/';

my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		#пароль /etc/freepbx.conf
my $db = '';		#"asterisk"; # имя базы данных.
my $user_email = '';	#e-mail для факсов.
my $domen = '';		#Домен.
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
			}when('user_email'){
				$user_email = $array_freepbx_pass[1];
			}default{
				next;
			}
		}
	}
close($freepbx_pass);

#SELECT email FROM userman_users WHERE username='XXXX';

my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
my $sth = $dbasterisk->prepare("SELECT email FROM userman_users WHERE username=\'$user_name\';");
$sth->execute; # исполняем запрос
while (my $ref = $sth->fetchrow_arrayref) {
	if (($$ref[0] ne '') && ($$ref[0] =~ /\@$domen$/)){
		$user_email = $$ref[0];
	}else{
		$comment = "Этот документ, для отправки факсимильного сообщения, был отправлен с учетной записи: \\
				$user_name, но у этой учетной записи в AD не корректно задан email.";
		#Если поле email пустое или не содержит @fmp.ru, то почту отправляем на $user_email
	}
#	print "$user_email\n"; # печатаем результат
}
my $rc = $sth->finish;
$rc = $dbasterisk->disconnect;  # закрываем соединение

open (my $file_3, '>>:encoding(UTF-8)', "$dir/number-fax.log") || die "Error opening file: number-fax.log $!";
	print $file_3 "$file_name\t$user_name\t$user_email\t$date_time_file\n";
close ($file_3);


my $yes_number_fax_file = `ls -la $dir| grep number-fax.conf\$`;
if ($yes_number_fax_file eq ''){
	open (my $file, '>:encoding(UTF-8)', "$dir/number-fax.conf") || die "Error opening file: number-fax.conf $!";
		print $file "$user_name\t$number_fax_start\n";
		$hash_number_fax{$user_name} = $number_fax_start;
	close ($file);
}else{
	open (my $file, '<:encoding(UTF-8)', "$dir/number-fax.conf") || die "Error opening file: number-fax.conf $!";
		while (defined(my $lime_number_fax = <$file>)){
			chomp ($lime_number_fax);
			my @array_number_fax = split (/\t/,$lime_number_fax,-1);
			$hash_number_fax{$array_number_fax[0]} = $array_number_fax[1];
		}
	close ($file);
}

if (exists ($hash_number_fax{$user_name})){
	$num = $hash_number_fax{$user_name};
}else{
	foreach my $key_user_name (sort keys %hash_number_fax){
		$i++;
	}
	$num = $number_fax_start + $i;
	open (my $file, '>>:encoding(UTF-8)', "$dir/number-fax.conf") || die "Error opening file: number-fax.conf $!";
		print $file "$user_name\t$num\n";
	close ($file);
}

move("$file_name","$dir_tiff/$num.pdf") or die "move failed: $!";
system("/usr/bin/gs -dSAFER -dBATCH -dQUIET -sDEVICE=tiffg3 -sPAPERSIZE=a4 -r204x196 -dNOPAUSE -sOutputFile=$dir_tiff/$num.tiff $dir_tiff/$num.pdf");
system("cp $dir_tiff/$num.pdf $dir/history_fax/${date_time_file}_$num.pdf");
chmod(0644,"$dir_tiff/$num.tiff");
system("/usr/bin/sendEmail -f fax_out\@$domen -t $user_email -u Исходящий факс -o message-charset=utf-8 \\
	-m \"\<html\>Для отправки факсимильного сообщения, в процессе разговора, необходимо перевести вызов на номер: $num\<br\>\<br\>$comment\<\/html\>\" \\
	-s localhost -a $dir_tiff/$num.pdf");
	
#system("/usr/bin/sendEmail -f fax_out\@itmh.ru -t kruk.ivan\@itmh.ru -u Исходящий факс -o message-charset=utf-8 -m Для отправки факса, в процессе разговора, необходимо перевести вызов на номер: $num -s localhost -a $dir_tiff/$num.pdf");
