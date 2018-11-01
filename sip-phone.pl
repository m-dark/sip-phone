#!/usr/bin/perl -w

#Формирование файлов конфигурации для sip-телефонов Yealink.
#Файл conf_number_line.conf содержит в себе информацию о том, какие номера прописаны за какими sip-телефонами (mac-адресами) и за каким номером аккаунта на этом sip-телефоне закреплен номер.
#(В AD есть только номер и mac, но этой информации не достаточно в том случае, если на тел. аппарате прописано несколько аккаунтов (номеров), как на W52P например), в связи с чем, 
#при прописывании дополнительного номера телефона в AD за одним и тем-же mac-адресом, конфигурация будет сформирована таким образом, что новый номер будет прописан за первым свободным номером аккаунта 
#на sip-телефоне и это будет зафиксировано в файле конфигурации conf_number_line.conf. Если для номеров телефонов на устройстве необходимо будет сменить номер аккаунта, то необходимо отредактировать 
#файл conf_number_line.conf согласно потребностям.
#Все изменения в файлах конфигурации для yealink, которые делает данный скрипт, фиксируются в каталоге history (сохраняется версия файла до редактирования и файл, который содержит информацию о том, 
#какие изменения были внесены, название файла содержит дату и время внесенных изменений)
#Предусмотрено:
#1)	Автоматическое формирование файла boot и cfg для всех моделей sip-телефонов yealink.
#2)	Если из AD удаляется mac-адрес sip-телефона, то в файле конфигурации для этого устройства удаляется номер телефона и пароль для регистрации на sip-сервере, для того чтобы sip-телефон удалил учетные данные 
#sip-учетки и не позволял совершать вызовы.
#3)	Проверка версии моделей sip-телефонов yealink на разных учетках AD для одинаковых mac-адресов sip-телефонов.
#Скрипт написал Крук Иван Александрович <kruk.ivan@itmh.ru>

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

my $dir = '/autoconfig';							#Директория для файлов .boot и .cfg
#my $dir = '/autoconfig_old';
my $dir_conf = '/etc/asterisk/script';						#Директория для файла conf_number_line.conf (который содержит информацию о том, за каким номером аккаунта прописан номер телефона).
my %hash_mac_model = ();							#Хэш mac-адресов с версией модели Yealinka. (Для проверки корректно внесенной информации о модели sip-телефона на разных учетках AD).
my %hash_sip_phone = ();							#Хэш содержит mac-адреса sip-телефонов с номерами телефонов и паролями от sip-учеток этих номеров.
my %hash_number_line = ();							#Хэш содержит mac-адреса sip-телефонов с номерами телефонов и номерами аккаунтов, к которым привязаны эти номера.
my %hash_dir_files = ();							#Хэш содержит список файлов конфигураций для всех sip-телефонов из каталога autoconf (для удаления sip-учетки на sip-телефонах, которые удалили из AD)
my $date_directory = strftime "%Y%m", localtime(time);				#Название каталога с историей изменений. (ГГГГММ)
my $date_time_file = strftime "%Y-%m-%d_%H%M%S", localtime(time);		#Переменная хранит в себе дату и время запуска скрипта, для понимания, когда вносились изменения.
my $script_dir = '/etc/asterisk/script';
my $history_dir = "$script_dir/history";
my $tmp_dir = '/tmp';
my $namedgroup = 'namedgroup.conf';
my $vpn_admin = 0;
my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		#пароль /etc/freepbx.conf
my $db = '';		#"asterisk"; # имя базы данных.
my $vpn_root = '';	#0|1 (0 - no vpn, 1 - yes vpn)
my $tftp_ip = '';	#'tftp://X.X.X.X/';
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
			}when('db'){
				$db = $array_freepbx_pass[1];
			}when('vpn_root'){
				$vpn_root = $array_freepbx_pass[1];
			}when('tftp_ip'){
				$tftp_ip = $array_freepbx_pass[1];
			}default{
				next;
			}
		}
	}
close($freepbx_pass);
my %hash_named = ();								#номера групп из файла conf_number_line.conf, имеют приоритет!
my %hash_named_db = ();								#номера групп из BD FreePBX
my %hash_namedgroup = ();							#номера групп из файла namedgroup.conf, содержит шаблоны по автозаполнению групп!
my %hash_vpn_user_enable = ();							#мак адрес у которого вклбючен VPN
my %hash_sipid_displayname = ();						#номер телефона и ФИО сотрудника Иванов И.И.
my %hash_model_conf = (
			't18'		=> 'y000000000009.cfg',
			't19'	=> 'y000000000053.cfg',
#			't19' 		=> 'y000000000031.cfg',
			't19_e2' 	=> 'y000000000053.cfg',
			't20'		=> 'y000000000007.cfg',
			't21'		=> 'y000000000034.cfg',
			't21_e2'	=> 'y000000000052.cfg',
			't22'		=> 'y000000000005.cfg',
			't23'		=> 'y000000000044.cfg',
			't23p'		=> 'y000000000044.cfg',
			't23g'		=> 'y000000000044.cfg',
			't26'		=> 'y000000000004.cfg',
			't27'	=> 'y000000000045.cfg',
			't27p'		=> 'y000000000045.cfg',
			't27g'		=> 'y000000000069.cfg',
			't29'	=> 'y000000000046.cfg',
			't29g'		=> 'y000000000046.cfg',
			't32'		=> 'y000000000032.cfg',
			't38'		=> 'y000000000038.cfg',
			't40'	=> 'y000000000054.cfg',
			't40p'		=> 'y000000000054.cfg',
			't40g'		=> 'y000000000076.cfg',
			't41'	=> 'y000000000036.cfg',
			't41p'		=> 'y000000000036.cfg',
			't41s'		=> 'y000000000068.cfg',
			't42'	=> 'y000000000029.cfg',
			't42g'		=> 'y000000000029.cfg',
			't42s'		=> 'y000000000067.cfg',
			't46'	=> 'y000000000066.cfg',
			't46g'		=> 'y000000000028.cfg',
			't46s'		=> 'y000000000066.cfg',
			't48'	=> 'y000000000035.cfg',
			't48g'		=> 'y000000000035.cfg',
			't48s'		=> 'y000000000065.cfg',
			't52s'		=> 'y000000000074.cfg',
			't54s'		=> 'y000000000070.cfg',
			'vp-t49'	=> 'y000000000051.cfg',
			'w52'		=> 'y000000000025.cfg',
			'w56'		=> 'y000000000025.cfg',
			'w60'		=> 'y000000000077.cfg',
			'vp530'		=> 'y000000000023.cfg',
			'cp860'		=> 'y000000000037.cfg',
			'cp920'		=> 'y000000000078.cfg',
			);

chdir "$dir" or die "No open $dir $!";
my @dir_files = glob "[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z].cfg";
foreach my $file_old (@dir_files){
	$file_old =~ s/.cfg//;
	$hash_dir_files{$file_old} = 1;
}

opendir (CD, "$history_dir") || mkdir "$history_dir", 0744;
closedir (CD);
opendir (HIS, "$history_dir/$date_directory") || mkdir "$history_dir/$date_directory/", 0744;
closedir (HIS);

my $yes_ad_sip_phone = `ls -la $dir_conf| grep ad_sip-phone.txt\$`;
if ($yes_ad_sip_phone eq ''){
	open (my $file, '>:encoding(UTF-8)', "$dir_conf/ad_sip-phone.txt") || die "Error opening file: ad_sip-phone.txt $!";
	close ($file);
}

#Считываем номера, у которых в атрибуте с моделью sip-телефона пусто.
my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass,{ mysql_enable_utf8 => 1 });
my $sth_ad = $dbasterisk->prepare("SELECT sip.id,sip.data,userman_users.fax,userman_users.home FROM sip,userman_users where sip.id = userman_users.work AND sip.keyword = 'secret' AND userman_users.home = '';");
$sth_ad->execute; # исполняем запрос
while (my $ref = $sth_ad->fetchrow_arrayref) {
	my $ok = 0;
	open (my $file_ad_sip_phone_txt, '<:encoding(UTF-8)', "$dir_conf/ad_sip-phone.txt") || die "Error opening file: ad_sip-phone.txt $!";
		while (defined(my $line_file_ad_sip_phone_txt = <$file_ad_sip_phone_txt>)){
			chomp ($line_file_ad_sip_phone_txt);
			my @array_line_file_ad_sip_phone_txt = split (/\t/,$line_file_ad_sip_phone_txt,-1);
			if ("$$ref[0]" == $array_line_file_ad_sip_phone_txt[0]){
				print "Скрытый номер: $$ref[0]\n";
				$ok = 1;
				$hash_mac_model{$array_line_file_ad_sip_phone_txt[2]} = $array_line_file_ad_sip_phone_txt[3];
				$hash_sip_phone{$array_line_file_ad_sip_phone_txt[2]}{$array_line_file_ad_sip_phone_txt[0]} = $array_line_file_ad_sip_phone_txt[1];
				$hash_named_db{$array_line_file_ad_sip_phone_txt[0]}{namedcallgroup} = $array_line_file_ad_sip_phone_txt[4];
				$hash_named_db{$array_line_file_ad_sip_phone_txt[0]}{namedpickupgroup} = $array_line_file_ad_sip_phone_txt[5];
				last;
			}
		}
		if ($ok == 0){
			print "ERROR 6, У номера $$ref[0] необходимо в AD заполнить все атрибуты.\n";
		}
	close ($file_ad_sip_phone_txt);
}
my $rc = $sth_ad->finish;

open (my $file_1, '<:encoding(UTF-8)', "$dir_conf/conf_number_line.conf") || die "Error opening file: conf_number_line.conf $!";
	while (defined(my $lime_number_line = <$file_1>)){
		chomp ($lime_number_line);
		my @array_number_line = split (/\t/,$lime_number_line,-1);
		$hash_number_line{$array_number_line[0]}{$array_number_line[1]} = $array_number_line[2];
		if (defined $array_number_line[3]){
			$hash_named{$array_number_line[1]}{namedcallgroup} = $array_number_line[3];
		}else{
			$hash_named{$array_number_line[1]}{namedcallgroup} = '';
		}
		if (defined $array_number_line[4]){
			$hash_named{$array_number_line[1]}{namedpickupgroup} = $array_number_line[4];
		}else{
			$hash_named{$array_number_line[1]}{namedpickupgroup} = '';
		}
	}
close ($file_1);

open (my $file_group, '<:encoding(UTF-8)', "$dir_conf/$namedgroup") || die "Error opening file: $namedgroup $!";
	while (defined(my $line_namedgroup = <$file_group>)){
		if ($line_namedgroup =~ /^\d/){
			chomp ($line_namedgroup);
			my @array_namedgroup = split (/\t/,$line_namedgroup,-1);
			if ($array_namedgroup[0] =~ /^(\d+\-\d+)$/){
				print "1\n";
				my @array_namedgroup_number = split (/\-/,$array_namedgroup[0],-1);
				if ($array_namedgroup_number[0] < $array_namedgroup_number[1]){
					while ($array_namedgroup_number[0] <= $array_namedgroup_number[1]){
						$hash_namedgroup{$array_namedgroup_number[0]}{namedcallgroup} = $array_namedgroup[1];
						$hash_namedgroup{$array_namedgroup_number[0]}{namedpickupgroup} = $array_namedgroup[2];
						$hash_namedgroup{$array_namedgroup_number[0]}{counter} += 1;
						$array_namedgroup_number[0]++;
						print "$array_namedgroup_number[0]\n";
					}
				}else{
					print "ERROR_4, $array_namedgroup_number[0] > $array_namedgroup_number[1]\n";
				}
			}elsif ($array_namedgroup[0] =~ /^(\dX)/){
				my $start_namedgroup_number = $array_namedgroup[0];
				my $end_namedgroup_number = $array_namedgroup[0];
				$start_namedgroup_number =~ s/X/0/g;
				$end_namedgroup_number =~ s/X/9/g;
				while ($start_namedgroup_number <= $end_namedgroup_number){
					$hash_namedgroup{$start_namedgroup_number}{namedcallgroup} = $array_namedgroup[1];
					$hash_namedgroup{$start_namedgroup_number}{namedpickupgroup} = $array_namedgroup[2];
					$hash_namedgroup{$start_namedgroup_number}{counter} += 1;
					$start_namedgroup_number++;
				}
			}elsif ($array_namedgroup[0] =~ /^(\d+)$/){
				$hash_namedgroup{$array_namedgroup[0]}{namedcallgroup} = $array_namedgroup[1];
				$hash_namedgroup{$array_namedgroup[0]}{namedpickupgroup} = $array_namedgroup[2];
				$hash_namedgroup{$array_namedgroup[0]}{counter} += 1;
			}else{
				print "ERROR_5, $array_namedgroup[0]\n";
			}
		}
	}
close ($file_group);
#проверка на дубли номеров
foreach my $key_namedgroup (sort keys %hash_namedgroup){
	if ($hash_namedgroup{$key_namedgroup}{counter} > 1){
		print "ERROR_6, в файле namedgroup.conf номер $key_namedgroup повторяется $hash_namedgroup{$key_namedgroup}{counter} раз(а)\n";
		exit;
	}
}

my $sth_sipid = $dbasterisk->prepare("SELECT sip.id,displayname FROM sip,userman_users where sip.id = userman_users.work AND sip.keyword = 'secret';");
$sth_sipid->execute; # исполняем запрос
while (my $ref = $sth_sipid->fetchrow_arrayref) {
	if ($$ref[1] =~ /^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+$/){
		my @array_fio = split (/ /,$$ref[1],-1);
		my $name = substr($array_fio[1],0,1);
		my $otc = substr($array_fio[2],0,1);
#		print "$array_fio[0] $name\.$otc\.\n";
		$hash_sipid_displayname{$$ref[0]} = "$array_fio[0] $name\.$otc\.";
	}elsif($$ref[1] =~ /^kas$/){
		$hash_sipid_displayname{$$ref[0]} = 'Кранштапов А.C.';
	}elsif ($$ref[1] =~ /^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+\s\d+$/){
		my @array_fio = split (/ /,$$ref[1],-1);
		my $name = substr($array_fio[1],0,1);
		my $otc = substr($array_fio[2],0,1);
#		print "$array_fio[0] $name\.$otc\.$array_fio[3]\n";
		$hash_sipid_displayname{$$ref[0]} = "$array_fio[0] $name\.$otc\.$array_fio[3]";
	}elsif($$ref[1] =~ /^.{0,15}$/){
		$hash_sipid_displayname{$$ref[0]} = $$ref[1];
#		print "$$ref[0]\t$$ref[1]\n";
	}else{
		my $fio = substr($$ref[1],0,15);
		$hash_sipid_displayname{$$ref[0]} = $fio;
#		print "$$ref[0]\t$fio\n";
	}
}
$rc = $sth_sipid->finish;

#print "Content-type: text/html\n\n";
#my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
#my $sth = $dbasterisk->prepare("SELECT sip.id,sip.data,userman_users.fax,userman_users.home FROM sip,userman_users where sip.id = userman_users.work AND sip.keyword = 'secret';");
my $sth = $dbasterisk->prepare("select a.id, max(secret) secret, fax, home, max(namedcallgroup) namedcallgroup, max(namedpickupgroup) namedpickupgroup from (select distinct id, case when keyword = 'secret' then data end secret, case when keyword = 'namedcallgroup' then data end namedcallgroup, case when keyword = 'namedpickupgroup' then data end namedpickupgroup from sip where keyword in ('secret','namedcallgroup','namedpickupgroup')) a left join userman_users u on u.work = a.id group by a.id, fax, home;");
$sth->execute; # исполняем запрос

#open ($file, '>>:encoding(UTF-8)', "$dir_conf/ad_sip-phone.txt") || die "Error opening file: ad_sip-phone.txt $!";
open (my $file, '>>:encoding(UTF-8)', "$tmp_dir/${date_time_file}_ad_sip-phone.txt") || die "Error opening file: ${date_time_file}_ad_sip-phone.txt $!";
	while (my $ref = $sth->fetchrow_arrayref) {
		if((defined ($$ref[3])) && ($$ref[3] =~ /\./)){
			my @array_ref_3 = split (/\./,$$ref[3],-1);
			$$ref[3] = $array_ref_3[0];
			if (($array_ref_3[1] eq 'vpn') || ($array_ref_3[1] eq 'VPN')){
				$hash_vpn_user_enable{"\L$$ref[2]"} = 1;
			}else{
				print "Error 111: VPN\n";;
			}
		}
#		print "$$ref[0]\t$$ref[1]\t$$ref[2]\t$$ref[3]\t$$ref[4]\n";
		if (defined ($$ref[2] && $$ref[3])){
			if (exists($hash_mac_model{"\L$$ref[2]"})){
				if (($hash_mac_model{"\L$$ref[2]"} ne "$$ref[3]") && ("$$ref[3]" ne '')){
					print "ERROR_2: За mac-адресом \L$$ref[2] уже прописана модель $hash_mac_model{\"\L$$ref[2]\"}, а вы пытаетесь прописать за ним новую модель $$ref[3]\n";
					next;
				}else{
#					print "Тест на скрытый номер: $$ref[2]\t $$ref[3]\n";
				}
			}else{
				$hash_mac_model{"\L$$ref[2]"} = "$$ref[3]";
			}
			$hash_sip_phone{"\L$$ref[2]"}{"$$ref[0]"} = "$$ref[1]";
			$hash_named_db{"$$ref[0]"}{namedcallgroup} = "$$ref[4]";
			$hash_named_db{"$$ref[0]"}{namedpickupgroup} = "$$ref[5]";
#			print $file "$$ref[0]\t$$ref[1]\t\L$$ref[2]\t$$ref[3]\t$$ref[4]\t$$ref[5]\n"; # печатаем результат
		}else{
			print "ERROR_3: В Asteriske номер $$ref[0] создан, а в AD его не стало. (можно удалить из exten, если этот номер там не нужен)\n";
			next;
		}
	}
	foreach my $key_sip_phone_mac (sort keys %hash_sip_phone){
		foreach my $key_sip_phone_number (sort keys %{$hash_sip_phone{$key_sip_phone_mac}}){
			print $file "$key_sip_phone_number\t$hash_sip_phone{$key_sip_phone_mac}{$key_sip_phone_number}\t$key_sip_phone_mac\t$hash_mac_model{$key_sip_phone_mac}\t$hash_named_db{$key_sip_phone_number}{namedcallgroup}\t$hash_named_db{$key_sip_phone_number}{namedpickupgroup}\n"; # печатаем результат
		}
	}
close ($file);

$rc = $sth->finish;
$rc = $dbasterisk->disconnect;  # закрываем соединение

#Удаляем sip-учетки в тех файлах конфигураций, которые были удалены из AD.
foreach my $key_dir_files (sort keys %hash_dir_files){
	if (exists($hash_mac_model{$key_dir_files})){
	
	}else{
		&number_zero($key_dir_files);
		&diff_file("$dir", "$tmp_dir", "$key_dir_files.cfg");
	}
}

#Удаляем номер телефона и номер Аккаунта, к которому привязан данный номер телефона, если номер был удален в AD.
foreach my $key_mac_address (sort keys %hash_number_line){
	foreach my $key_number (keys %{$hash_number_line{$key_mac_address}}){
		if (exists($hash_sip_phone{$key_mac_address}{$key_number})){
		}else{
			delete $hash_number_line{$key_mac_address}{$key_number};
		}
	}
}

#Прописываем новые номера и номер аккаунта для номера.
foreach my $key_mac_address (sort keys %hash_sip_phone){
	foreach my $key_number (keys %{$hash_sip_phone{$key_mac_address}}){
		if (exists($hash_number_line{$key_mac_address}{$key_number})){
#		&add_line ("$key_mac_address","$key_number");
		}else{
			&add_line ("$key_mac_address","$key_number");
		}
	}
}

#Создаем .boot файл для sip-телефона.
foreach my $key_mac_model (sort keys %hash_mac_model){
    &conf_boot("$key_mac_model","$hash_mac_model{$key_mac_model}");
}

#Создаем файл конфигурации для sip-телефона.
open ($file_1, '>:encoding(UTF-8)', "$tmp_dir/${date_time_file}_conf_number_line.conf") || die "Error opening file: ${date_time_file}_conf_number_line.conf $!";
	foreach my $key_number_line_mac (sort keys %hash_number_line){
		if ($vpn_root == 1){
			opendir (VPN_CFG, "$dir/$key_number_line_mac/") || ((mkdir "$dir/$key_number_line_mac/", 0744) && (`cp -f $dir/template_vpn_conf/client.tar $dir/$key_number_line_mac/ && chown -R tftpd:tftpd $dir/$key_number_line_mac`));
			closedir (VPN_CFG);
		}
		open (my $file_cfg, '>:encoding(utf-8)', "$tmp_dir/${date_time_file}_${key_number_line_mac}.cfg") || die "Error opening file: ${date_time_file}_${key_number_line_mac}.cfg $!";
			print $file_cfg "#!version:1.0.0.1\n";
			foreach my $key_number_line_number(sort { $hash_number_line{$key_number_line_mac}{$a} <=> $hash_number_line{$key_number_line_mac}{$b} } keys %{$hash_number_line{$key_number_line_mac}}){
				my $namedcallgroup = '';
				my $namedpickupgroup = '';
				if(exists ($hash_namedgroup{$key_number_line_number})){
					$namedcallgroup = $hash_namedgroup{$key_number_line_number}{namedcallgroup};
					$namedpickupgroup = $hash_namedgroup{$key_number_line_number}{namedpickupgroup};
				}
				if ((exists ($hash_named{$key_number_line_number})) && ($hash_named{$key_number_line_number}{namedcallgroup} ne '')){
					$namedcallgroup = $hash_named{$key_number_line_number}{namedcallgroup};
				}
				if ((exists ($hash_named{$key_number_line_number})) && ($hash_named{$key_number_line_number}{namedpickupgroup} ne '')){
					$namedpickupgroup = $hash_named{$key_number_line_number}{namedpickupgroup};
				}
				if ($namedcallgroup ne $hash_named_db{$key_number_line_number}{namedcallgroup}){
#					print "!!!!!!!!!!!!!$namedcallgroup $hash_named_db{$key_number_line_number}{namedcallgroup}\n";
					&update_namedcallgroup ($key_number_line_number, $namedcallgroup, $hash_named_db{$key_number_line_number}{namedcallgroup});
				}
				if ($namedpickupgroup ne $hash_named_db{$key_number_line_number}{namedpickupgroup}){
#					print "!!!!!!!!!!!!!$namedpickupgroup $hash_named_db{$key_number_line_number}{namedpickupgroup}\n";
					&update_namedpickupgroup ($key_number_line_number, $namedpickupgroup, $hash_named_db{$key_number_line_number}{namedpickupgroup});
				}
				print $file_1 "$key_number_line_mac\t$key_number_line_number\t$hash_number_line{$key_number_line_mac}{$key_number_line_number}\t$namedcallgroup\t$namedpickupgroup\n";
				open (my $file_xxx_ppp, '<:encoding(UTF-8)', "$dir/XXXPPP.cfg") || die "Error opening file: XXXPPP.cfg $!";
					while (defined(my $lime_cfg = <$file_xxx_ppp>)){
						chomp ($lime_cfg);
						if ($lime_cfg =~ /^(account.0.display_name = |account.0.auth_name = |account.0.user_name = )$/){
							$lime_cfg =~ s/account.0//;
							$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."$key_number_line_number";
						}elsif ($lime_cfg =~ /^account.0.label = $/){
							$lime_cfg =~ s/account.0//;
							if ($key_number_line_number == 555){
								$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."Приёмная";
							}elsif($key_number_line_number == 191){
								$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."357-30-97";
							}elsif($key_number_line_number == 192){
								$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."385-79-00";
							}else{
								$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."$key_number_line_number";
							}
						}elsif ($lime_cfg =~ /^account.0.password = $/){
							$lime_cfg =~ s/account.0//;
							$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg"."$hash_sip_phone{$key_number_line_mac}{$key_number_line_number}";
						}elsif ($lime_cfg =~ /^account.0./){
							$lime_cfg =~ s/account.0//;
							$lime_cfg = "account."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}"."$lime_cfg";
						}
						print $file_cfg "$lime_cfg\n";
					}
				close ($file_xxx_ppp);
			}
			if (exists($hash_vpn_user_enable{$key_number_line_mac})){
				print $file_cfg "network.vpn_enable = 1\n";
				print $file_cfg "openvpn.url = ${tftp_ip}${key_number_line_mac}/client.tar\n";
			}else{
				print $file_cfg "network.vpn_enable = 0\n";
				print $file_cfg "openvpn.url = ${tftp_ip}${key_number_line_mac}/client.tar\n";
			}
##!!			print $file_cfg "programablekey.2.type = 38\nprogramablekey.2.label = Конт.\nprogramablekey.3.type = 43\nprogramablekey.3.line = 1\n";
		close ($file_cfg);
		open (my $file_cfg_local, '>:encoding(utf-8)', "$tmp_dir/${date_time_file}_${key_number_line_mac}-local.cfg") || die "Error opening file: ${date_time_file}_${key_number_line_mac}-local.cfg $!";
			print $file_cfg_local "#!version:1.0.0.1\n";
			if (($hash_mac_model{${key_number_line_mac}} eq 'w52') || ($hash_mac_model{${key_number_line_mac}} eq 'w56') || ($hash_mac_model{${key_number_line_mac}} eq 'w60')){
				foreach my $key_number_line_number(sort { $hash_number_line{$key_number_line_mac}{$a} <=> $hash_number_line{$key_number_line_mac}{$b} } keys %{$hash_number_line{$key_number_line_mac}}){
					if ($key_number_line_number == 555){
						print $file_cfg_local "handset."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}".".name = "."Приёмная\n";
					}else{
						print $file_cfg_local "handset."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}".".name = "."$key_number_line_number\n";
					}
				}
			}
			my $yes_file_cfg_local = `ls -la $dir| grep ${key_number_line_mac}-local.cfg\$`;
			if ($yes_file_cfg_local ne ''){
				my %hash_linekey = ();
				my $linekey_start = 0;
				open (my $file_cfg_local_old, '<:encoding(UTF-8)', "$dir/${key_number_line_mac}-local.cfg") || die "Error opening file: ${key_number_line_mac}-local.cfg $!";
					while (defined(my $line_cfg_local_old = <$file_cfg_local_old>)){
						chomp ($line_cfg_local_old);
						if ($line_cfg_local_old =~ /^\#\!version:/){
							next;
						}elsif ($line_cfg_local_old =~ / = /){
							my @mas_line_cfg_local_old = split (/ = /,$line_cfg_local_old,-1);
							if($mas_line_cfg_local_old[0] eq 'static.network.vpn_enable'){
								if ($linekey_start == 1){
									print "!!!!!$file_cfg_local!!!!!!\n";
									&print_array_linekey($file_cfg_local,\%hash_linekey);
									$linekey_start = 0;
								}
								next;
							}elsif($mas_line_cfg_local_old[0] =~ /^account.\d{1,2}.always_fwd.enable$/){
								print $file_cfg_local "$mas_line_cfg_local_old[0] = 0\n";
							}elsif($mas_line_cfg_local_old[0] =~ /^account.\d{1,2}.always_fwd.target$/){
								print $file_cfg_local "$mas_line_cfg_local_old[0] = \%EMPTY\%\n";
							}elsif($mas_line_cfg_local_old[0] =~ /^handset.\d.name$/){
								if ($linekey_start == 1){
									&print_array_linekey($file_cfg_local,\%hash_linekey);
									$linekey_start = 0;
								}
								next;
							}elsif($mas_line_cfg_local_old[0] =~ /^linekey.\d{1,2}./){
								$linekey_start = 1;
								my @number_linekey = split (/\./,$mas_line_cfg_local_old[0],-1);
								$hash_linekey{"$number_linekey[0].$number_linekey[1]"}{$number_linekey[2]} = $mas_line_cfg_local_old[1];
#								print "$number_linekey[0].$number_linekey[1]\t$number_linekey[2] = $mas_line_cfg_local_old[1]\n";
##								print $file_cfg_local "$line_cfg_local_old\n";
							}else{
								if ($linekey_start == 1){
									&print_array_linekey($file_cfg_local,\%hash_linekey);
									$linekey_start = 0;
								}
								print $file_cfg_local "$line_cfg_local_old\n";
							}
						}else{
							if ($linekey_start == 1){
								&print_array_linekey($file_cfg_local,\%hash_linekey);
								$linekey_start = 0;
							}
							print $file_cfg_local "$line_cfg_local_old\n";
						}
					}
					if ($linekey_start == 1){
						&print_array_linekey($file_cfg_local,\%hash_linekey);
						$linekey_start = 0;
					}
				close ($file_cfg_local_old);
			}else{
				if (($hash_mac_model{${key_number_line_mac}} eq 'w52') || ($hash_mac_model{${key_number_line_mac}} eq 'w56') || ($hash_mac_model{${key_number_line_mac}} eq 'w60')){
					foreach my $key_number_line_number(sort { $hash_number_line{$key_number_line_mac}{$a} <=> $hash_number_line{$key_number_line_mac}{$b} } keys %{$hash_number_line{$key_number_line_mac}}){
						if ($key_number_line_number == 555){
							print $file_cfg_local "handset."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}".".name = "."Приёмная\n";
						}else{
							print $file_cfg_local "handset."."$hash_number_line{$key_number_line_mac}{$key_number_line_number}".".name = "."$key_number_line_number\n";
						}
					}
				}
			}
		close ($file_cfg_local);

		my $yes_file_cfg = `ls -la $dir| grep ${key_number_line_mac}.cfg\$`;
		if ($yes_file_cfg eq ''){
			open (my $file_cfg, '>:encoding(UTF-8)', "$dir/${key_number_line_mac}.cfg") || die "Error opening file: ${key_number_line_mac}.cfg $!";
			close ($file_cfg);
			print "!!!!!!!!$dir/${key_number_line_mac}.cfg\n";
		}
		&diff_file("$dir", "$tmp_dir", "${key_number_line_mac}.cfg");
		$yes_file_cfg_local = `ls -la $dir| grep ${key_number_line_mac}-local.cfg\$`;
		if ($yes_file_cfg_local eq ''){
			open (my $file_cfg_local, '>:encoding(UTF-8)', "$dir/${key_number_line_mac}-local.cfg") || die "Error opening file: ${key_number_line_mac}-local.cfg $!";
			close ($file_cfg_local);
			print "Был создан файл: $dir/${key_number_line_mac}-local.cfg\n";
		}
		&diff_file("$dir", "$tmp_dir", "${key_number_line_mac}-local.cfg");
	}
close ($file_1);

#Фиксируем изменения. (был добавлен или удален номер телефона или устройство в AD)
&diff_file("$script_dir", "$tmp_dir", 'ad_sip-phone.txt');
#Фиксируем изменения. (был добавлен или удален номер телефона)
&diff_file("$script_dir", "$tmp_dir", 'conf_number_line.conf');
#отвечает за перезагрузку диалплата Asterisk и его модулей. Эта команда соответствует нажатию кнопки "Apply Changes" через GUI FreePBX.
#`amportal a r`;
#`fwconsole reload`;
`sudo -u root /usr/sbin/fwconsole reload`;

#print Dumper \%hash_sip_phone;

##my $i = 1;
##foreach my $key_mac_address (sort keys %hash_sip_phone){
##	foreach my $key_number (keys %{$hash_sip_phone{$key_mac_address}}){
####		print "$i\t$key_mac_address\t$key_number\t$hash_sip_phone{$key_mac_address}{$key_number}\n";
##		$i++;
##	}
##}

#linekey.1.type = 15
#linekey.1.value = %EMPTY%
#linekey.1.line = 1
#linekey.1.label = %EMPTY%
#linekey.1.extension = %EMPTY%
#linekey.1.xml_phonebook = 0
#linekey.1.pickup_value = %EMPTY%

sub print_array_linekey{
	my $file_cfg_local = shift;
	my ($hash_linekey) = @_;
	foreach my $key_line_linekey (sort keys %$hash_linekey){
		if ((exists($$hash_linekey{$key_line_linekey}{value})) && (exists($hash_sipid_displayname{$$hash_linekey{$key_line_linekey}{value}})) && ($$hash_linekey{$key_line_linekey}{label} ne $hash_sipid_displayname{$$hash_linekey{$key_line_linekey}{value}})){
##			print "!!$$hash_linekey{$key_line_linekey}{value}\t$hash_sipid_displayname{$$hash_linekey{$key_line_linekey}{value}}!!\n";
			print "Замена $$hash_linekey{$key_line_linekey}{label} на $hash_sipid_displayname{$$hash_linekey{$key_line_linekey}{value}}\n"; 
			$$hash_linekey{$key_line_linekey}{label} = $hash_sipid_displayname{$$hash_linekey{$key_line_linekey}{value}};
		}
		my $i = 7;
		my @label_value = ();
		foreach my $linekey_type (sort keys %{$$hash_linekey{$key_line_linekey}}){
##			print "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}\n";
			if ($linekey_type eq 'type'){
				$label_value[0] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'value'){
				$label_value[1] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'line'){
				$label_value[2] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'label'){
				$label_value[3] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'extension'){
				$label_value[4] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'xml_phonebook'){
				$label_value[5] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}elsif($linekey_type eq 'pickup_value'){
				$label_value[6] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
			}else{
				$label_value[$i] = "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}";
#				print $file_cfg_local "$key_line_linekey.$linekey_type = $$hash_linekey{$key_line_linekey}{$linekey_type}\n";
				$i++;
			}
		}
		foreach my $line_new (@label_value){
			if (defined $line_new){
				print $file_cfg_local "$line_new\n";
			}
		}
	}
	%$hash_linekey = ();
}

sub add_line{
		my $mac_address = shift;
		my $number = shift;
		my $constanta_number = 0;
		my %hash_static_line = (
					'1' => '0',
					'2' => '0',
					'3' => '0',
					'4' => '0',
					'5' => '0',
					'6' => '0',
					'7' => '0',
					'8' => '0',
					'9' => '0',
					'10' => '0',
					'11' => '0',
					'12' => '0',
					'13' => '0',
					'14' => '0',
					'15' => '0',
					'16' => '0',
					'17' => '0',
					'18' => '0',
					'19' => '0',
					'20' => '0',
					'21' => '0',
					'22' => '0',
					'23' => '0',
					'24' => '0',
					'25' => '0',
					'26' => '0',
					);
		if (exists($hash_number_line{$mac_address})){
			foreach my $key_number_line_number(sort keys %{$hash_number_line{$mac_address}}){
				delete $hash_static_line{$hash_number_line{$mac_address}{$key_number_line_number}};
				if ("$number" eq "$key_number_line_number"){
					$constanta_number = 1;
				}
			}
			if ($constanta_number == 0){
				foreach my $key_number_line_static (sort {$a<=>$b} keys %hash_static_line){
					$hash_number_line{$mac_address}{$number} = $key_number_line_static;
					last;
				}
			}
		}else{
			$hash_number_line{$mac_address}{$number} = 1;
		}
}

#Функция удаления sip-учеток номеров c sip-телефонов, которые были удалены в AD.
sub number_zero{
	my $file = shift;
	open (my $file_tmp, '>:encoding(UTF-8)', "$tmp_dir/${date_time_file}_$file.cfg") || die "Error opening file: ${date_time_file}_$file.cfg $!";
		open (my $file_1, '<:encoding(UTF-8)', "$dir/$file.cfg") || die "Error opening file: $file.cfg $!";
			while (defined(my $line_cfg_file_old = <$file_1>)){
				chomp ($line_cfg_file_old);
				if ($line_cfg_file_old =~ / = /){
					my @mas_line_cfg_file_old = split (/ = /,$line_cfg_file_old,-1);
					if ($mas_line_cfg_file_old[0] =~ /^(account\.\d+\.enable|account\.\d+\.sip_server\.\d+\.register_on_enable)$/){
						print $file_tmp "$mas_line_cfg_file_old[0] = 0\n";
					}elsif ($mas_line_cfg_file_old[0] =~ /^(account\.\d+\.label|account\.\d+\.display_name|account\.\d+\.auth_name|account\.\d+\.user_name)$/){
						print $file_tmp "$mas_line_cfg_file_old[0] = 000\n";
					}elsif ($mas_line_cfg_file_old[0] =~ /(^account\.\d+\.password)$/){
						print $file_tmp "$mas_line_cfg_file_old[0] = 000\n";
					}else{
						print $file_tmp "$line_cfg_file_old\n";
					}
				}else{
					print $file_tmp "$line_cfg_file_old\n";
				}
			}
		close ($file_1);
	close ($file_tmp);
}

#Функция создания файла .boot
sub conf_boot{
	my $mac_address = shift;
	my $model = shift;
	if (exists($hash_model_conf{$model})){
		open (my $file_boot, '>:encoding(UTF-8)', "$tmp_dir/${date_time_file}_${mac_address}.boot") || die "Error opening file: ${date_time_file}_${mac_address}.boot $!";
			print $file_boot '#!version:1.0.0.1';
			print $file_boot "\n## the header above must appear as-is in the first line\n";
			print $file_boot "     \n";
			print $file_boot "include:config \"$hash_model_conf{$model}\"\n";
			print $file_boot "include:config \"${mac_address}.cfg\"\n";
			print $file_boot "     \n";
			print $file_boot "overwrite_mode = 1\n";
		close ($file_boot);

		my $yes_file_boot = `ls -la $dir| grep ${mac_address}.boot\$`;
		if ($yes_file_boot eq ''){
			open (my $file, '>:encoding(UTF-8)', "$dir/${mac_address}.boot") || die "Error opening file: $dir/${mac_address}.boot $!";
			close ($file);
		}
		&diff_file("$dir", "$tmp_dir", "${mac_address}.boot");
	}else{
		print "ERROR_1: $mac_address\t$model\n";
	}
}

#Функция обновления файлов конфигураций и фиксации изменений в history.
sub diff_file{
	my $dir_file = shift;
	my $tmp_dir_file = shift;
	my $original_file = shift;
	
	my $diff_file = `diff -u $dir_file/$original_file $tmp_dir_file/${date_time_file}_${original_file}`;
	if ($diff_file ne ''){
		`diff -u $dir_file/${original_file} $tmp_dir_file/${date_time_file}_${original_file} > $history_dir/$date_directory/${date_time_file}_${original_file}.diff`;
		`cat $dir_file/${original_file} > $history_dir/$date_directory/${date_time_file}_${original_file}`;
		`cat $tmp_dir_file/${date_time_file}_${original_file} > $dir_file/$original_file && chown tftpd:tftpd $dir_file/$original_file`;
	}
	`rm $tmp_dir_file/${date_time_file}_${original_file}`;
}
sub update_namedcallgroup{
	my $number = shift;
	my $namedcallgroup = shift;
	my $namedcallgroup_old = shift;
	my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
	my $sth = $dbasterisk->prepare("UPDATE sip set data = \'$namedcallgroup\' WHERE id = $number and keyword = \'namedcallgroup\';");
	$sth->execute; # исполняем запрос
	my $rc = $sth->finish;
	$rc = $dbasterisk->disconnect;  # закрываем соединение
	open (my $file_log_named, '>>:encoding(UTF-8)', "/$history_dir/$date_directory/${date_time_file}_named_update.log") || die "Error opening file: ${date_time_file}_named_update.log $!";
		print $file_log_named "$number\tnamedcallgroup\t$namedcallgroup -> $namedcallgroup_old\n";
	close ($file_log_named);
}
sub update_namedpickupgroup{
	my $number = shift;
	my $namedpickupgroup = shift;
	my $namedpickupgroup_old = shift;
	my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
	my $sth = $dbasterisk->prepare("UPDATE sip set data = \'$namedpickupgroup\' WHERE id = $number and keyword = \'namedpickupgroup\';");
	$sth->execute; # исполняем запрос
	my $rc = $sth->finish;
	$rc = $dbasterisk->disconnect;  # закрываем соединение
	open (my $file_log_named, '>>:encoding(UTF-8)', "/$history_dir/$date_directory/${date_time_file}_named_update.log") || die "Error opening file: ${date_time_file}_named_update.log $!";
		print $file_log_named "$number\tnamedpickupgroup\t$namedpickupgroup -> $namedpickupgroup_old\n";
	close ($file_log_named);
}
