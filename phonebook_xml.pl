#!/usr/bin/perl -w
#
# FreePBX Phonebook Creation Script
# (c) Kruk Ivan
# kruk.ivan@itmh.ru
# 1. Base FPBX install. Database in use = asterisk
# 2. Localhost requires no authentication
# 3. Standard Yealink XML Phonebook
# 4. Apache webdir = /var/www/html
use 5.010;
use strict;
use warnings;
use POSIX qw(strftime);
use locale;
use Time::Local;
use encoding 'utf-8';
use DBI;
use File::Copy;

my $dir = '/opt/asterisk/script';								#Директория для файла conf_number_line.conf (который содержит информацию о том, за каким номером аккаунта прописан номер телефона).
my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		#пароль /etc/freepbx.conf
my $db = '';		#"asterisk"; # имя базы данных.
#my @invisible = (121,152,521,523,524);
my @invisible = '';
my $invisible_yes = 0;
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
                        }when('invisible'){
				@invisible = split (/,/,$array_freepbx_pass[1]);
                        }default{
                                next;
                        }
                }
        }
close($freepbx_pass);

my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass,{ mysql_enable_utf8 => 1 });
my $sth = $dbasterisk->prepare("SELECT name,extension FROM users ORDER BY name;");
$sth->execute; # исполняем запрос
open (my $file, '>:encoding(UTF-8)', "$dir/phonebook.xml") || die "Error opening file: phonebook.xml $!";
print $file "\<\?xml version=\"1.0\"\?\>\n\<YealinkIPPhoneDirectory\>\n";
while (my $ref = $sth->fetchrow_arrayref){
        my $name = $$ref[0];
        my $extension = $$ref[1];
        $invisible_yes = 0;
        foreach my $invisible (@invisible){
		if($extension == $invisible){
			$invisible_yes++;
		}
	}
	if ($invisible_yes == 0){
		print $file "  \<DirectoryEntry\>
    \<Name\>$name\<\/Name\>
    \<Telephone\>$extension\<\/Telephone\>
  \<\/DirectoryEntry\>\n";
	}
}
open (my $file_phonebook_cfg, '<:encoding(UTF-8)', "$dir/phonebook.cfg") || die "Error opening file: phonebook.cfg $!";
        while (defined(my $line_phonebook_cfg = <$file_phonebook_cfg>)){
                chomp ($line_phonebook_cfg);
                my @array_phonebook_cfg = split (/\t/,$line_phonebook_cfg,-1);
                print $file "  \<DirectoryEntry\>
    \<Name\>$array_phonebook_cfg[0]\<\/Name\>
    \<Telephone\>$array_phonebook_cfg[1]\<\/Telephone\>
  \<\/DirectoryEntry\>\n";
        }
close ($file_phonebook_cfg);

print $file "\<\/YealinkIPPhoneDirectory\>\n";
close ($file);
my $rc = $sth->finish;
$rc = $dbasterisk->disconnect;  # закрываем соединение

`cp $dir/phonebook.xml /var/www/html/phonebook.xml`
#`chmod 644 /var/www/html/phonebook.xml`
