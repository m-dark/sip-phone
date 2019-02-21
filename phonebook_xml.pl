#!/usr/bin/perl -w
#
# FreePBX Phonebook Creation Script
# (c) Kruk Ivan
# kruk.ivan@itmh.ru
# 1. Base FPBX install. Database in use = asterisk
# 2. Localhost requires no authentication
# 3. Standard Yealink XML Phonebook
# 4. Apache webdir = /var/www/html
use strict;
use warnings;
use POSIX qw(strftime);
use locale;
use Time::Local;
use encoding 'utf-8';
use DBI;
use File::Copy;

my $dir = '/etc/asterisk/script';
my $host = "localhost"; # MySQL-сервер нашего хостинга
my $port = "3306"; # порт, на который открываем соединение
my $user = "freepbxuser"; # имя пользователя
my $pass = "zhlorp5lO765"; # пароль /etc/freepbx.conf
my $db = "asterisk"; # имя базы данных.

my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass,{ mysql_enable_utf8 => 1 });
my $sth = $dbasterisk->prepare("SELECT name,extension FROM users;");
$sth->execute; # исполняем запрос
open (my $file, '>:encoding(UTF-8)', "$dir/phonebook.xml") || die "Error opening file: phonebook.xml $!";
print $file "\<\?xml version=\"1.0\"\?\>\n\<YealinkIPPhoneDirectory\>\n";
while (my $ref = $sth->fetchrow_arrayref){
        my $name = $$ref[0];
        my $extension = $$ref[1];
        print $file "  \<DirectoryEntry\>
    \<Name\>$name\<\/Name\>
    \<Telephone\>$extension\<\/Telephone\>
  \<\/DirectoryEntry\>\n";
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
