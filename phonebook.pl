#!/usr/bin/perl -w

use 5.010;
use strict;
use warnings;
use Spreadsheet::WriteExcel;
use POSIX qw(strftime);
use locale;
use Time::Local;
#use Encode;
use encoding 'utf-8';
use DBI;
use File::Copy;

my $dir = '/etc/asterisk/script';
my $history_dir = "$dir/history";
my $dir_conf_asterisk = '/etc/asterisk';
my $file_extensions_additional = 'extensions_additional.conf';
my $host = '';		#"localhost"; # MySQL-сервер нашего хостинга
my $port = '';		#"3306"; # порт, на который открываем соединение
my $user = '';		#"freepbxuser"; # имя пользователя
my $pass = '';		# пароль /etc/freepbx.conf
my $db = '';		#"asterisk"; # имя базы данных.
my $domen = '';		#Домен
my $user_name = '';	#
my $user_email_phonebook = '';	#Куда отправляем телефонный справочник.
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
			}when('user_email_phonebook'){
				$user_email_phonebook = $array_freepbx_pass[1];
			}default{
				next;
			}
		}
	}
close($freepbx_pass);

my $number = $ARGV[0];
my $text = '<html><table width="1200" border="1"><caption>Изменения в телефонном справочнике сотрудников</caption><tr><th>ФИО</th><th>Внутренний номер</th><th>Прямой городской номер</th><th>Прямой групповой городской номер</th><th>Городской номер голосового меню</th></tr>';

my $date_directory = strftime "%Y%m", localtime(time);				#Название каталога с историей изменений. (ГГГГММ)
my $date_time_file = strftime "%Y-%m-%d_%H%M%S", localtime(time);		#Переменная хранит в себе дату и время запуска скрипта, для понимания, когда вносились изменения.
my $tmp_dir = '/tmp';
my %hash_displayname = ();		#ФИО           => 108
my %hash_did = ();			#num_c{number} => num
my %hash_ext_group = ();		#num_c{number} => num_g
my %hash_group = ();			#num_g{number} => num
my %hash_ivr = ();			#ivr  {number} => num
my %hash_ivr_number_group = ();		#num_g{ivr}    => key

my $partition = '';
my $parsing_yes = 0;
open (my $file_csv, '>:encoding(windows-1251)', "$tmp_dir/${date_time_file}_phonebook.csv") || die "Error opening file: ${date_time_file}_phonebook.csv $!";
	print $file_csv 'ФИО;Внутренний номер;Прямой городской номер;Прямой групповой городской номер;Городской номер голосового меню';
	print $file_csv "\n";
close ($file_csv);

my $dbasterisk = DBI->connect("DBI:mysql:$db:$host:$port",$user,$pass);
$dbasterisk->do("set character set utf8");
$dbasterisk->do("set names utf8");
my $sth = $dbasterisk->prepare("SELECT displayname, default_extension FROM userman_users;");
$sth->execute; # исполняем запрос
while (my $ref = $sth->fetchrow_arrayref) {
	if ($$ref[1] =~ /^(191|192)$/){
		next;
	}else{
		$hash_displayname{$$ref[0]}=$$ref[1];
	}
#	print "$$ref[0]\t$$ref[1]\n";
}
my $rc = $sth->finish;
$rc = $dbasterisk->disconnect;  # закрываем соединение

open (my $file, '<:encoding(UTF-8)', "$dir_conf_asterisk/$file_extensions_additional") || die "Error opening file: $file_extensions_additional $!";
	while (defined(my $line_extensions_additional = <$file>)){
		if ($line_extensions_additional =~ /^\r?$/){
			next;
		}
		chomp ($line_extensions_additional);
		if (($parsing_yes == 0) && ($line_extensions_additional =~ /^\[ext-did-0002\]$/)){
			$partition = 'ext-did-0002';
			$parsing_yes = 1;
			next;
#			print "$line_extensions_additional\n";
#			my @array_number_fax = split (/\t/,$line_number_fax,-1);
#			$user_name = $array_number_fax[0];
		}elsif (($parsing_yes == 1) && ($line_extensions_additional =~ /^\;--== end of \[ext-did-0002\] ==--\;$/)){
			$parsing_yes = 0;
			next;
		}elsif (($parsing_yes == 0) && ($line_extensions_additional =~ /^\[ext-group\]$/)){
			$partition = 'ext-group';
			$parsing_yes = 1;
			next;
		}elsif (($parsing_yes == 1) && ($line_extensions_additional =~ /^\;--== end of \[ext-group\] ==--\;$/)){
			$parsing_yes = 0;
			next;
		}
		if ($parsing_yes == 1){
			&parsing($partition,$line_extensions_additional);
		}else{
			next;
		}
	}
close ($file);

#Печатаем результат
#ФИО | ВН | ПГН | ГГН | IVR (1) |
chdir '/etc/asterisk/script';
my $workbook  = Spreadsheet::WriteExcel->new("phonebook_${domen}.xls");

my $worksheet = $workbook->add_worksheet("$domen");
my $bold = $workbook->add_format(bold => 1);

$worksheet->set_column('A:A', 56, $bold);
$worksheet->set_column('B:B', 22, $bold);
$worksheet->set_column('C:C', 29, $bold);
$worksheet->set_column('D:D', 42, $bold);
$worksheet->set_column('E:E', 41, $bold);
$worksheet->set_row   (0,     30       );

my $heading  = $workbook->add_format(
					bold    => 1,
					color   => 'black',
					size    => 12,
					align   => 'center',
					);

my $heading_2  = $workbook->add_format(
					bold    => 0,
					color   => 'black',
					size    => 10,
					align   => 'left',
					);
					
my @headings = ('ФИО', 'Внутренний номер', 'Прямой городской номер', 'Прямой групповой городской номер', 'Городской номер голосового меню');
$worksheet->write_row('A1', \@headings, $heading);

my $aai = 1;

foreach my $key_displayname (sort keys %hash_displayname){
	my @number_g = ();
	my @number_cg = ();
	my @number_gg = ();
	my @number_ivr = ();
	my $aa = 'A';
	@headings = ();
	if (exists $hash_did{$hash_displayname{$key_displayname}}){
		foreach my $key_did (sort keys %{$hash_did{$hash_displayname{$key_displayname}}}){
			push (@number_g, $key_did);
		}
#		print "@number_g\n";
	}
	if (exists $hash_ext_group{$hash_displayname{$key_displayname}}){
		foreach my $key_ext_group (sort keys %{$hash_ext_group{$hash_displayname{$key_displayname}}}){
			if (exists $hash_group{$key_ext_group}){
				foreach my $key_group (sort keys %{$hash_group{$key_ext_group}}){
					push (@number_gg, $key_group);
				}
#			print "$hash_displayname{$key_displayname}\t@number_gg\n";
			push (@number_cg, $key_ext_group);
			}
			
			if (exists $hash_ivr_number_group{$key_ext_group}){
				foreach my $key_ivr_number_group (sort keys %{$hash_ivr_number_group{$key_ext_group}}){
#					print "$hash_ivr_number_group{$key_ext_group}{$key_ivr_number_group}\n";
					foreach my $key_ivr (sort keys %{$hash_ivr{$key_ivr_number_group}}){
						push (@number_ivr, "$key_ivr"."\($hash_ivr_number_group{$key_ext_group}{$key_ivr_number_group}\)");
#						print "$key_ivr\n";
					}
				}
			}
#			print "@number_ivr\n";
		}
#		print "@number_cg\n";
	}
	$aai ++;
	$aa = "$aa"."$aai";
	my $key_displayname_2 = Encode::decode('utf-8', $key_displayname);
	@headings = ("$key_displayname_2", "$hash_displayname{$key_displayname}", "@number_g", "@number_gg", "@number_ivr");
#	print "@headings\n";
	
	open ($file_csv, '>>:encoding(windows-1251)', "$tmp_dir/${date_time_file}_phonebook.csv") || die "Error opening file: ${date_time_file}_phonebook.csv $!";
		print $file_csv "$key_displayname\;$hash_displayname{$key_displayname}\;@number_g;@number_gg\;@number_ivr\n";
	close ($file_csv);
	$worksheet->write_row($aa, \@headings, $heading_2);
}
$workbook->close();

&diff_file("$dir", "$tmp_dir", "phonebook.csv");

sub parsing {
	my $direction = shift;
	my $line = shift;
	
	if ($direction eq 'ext-did-0002'){
		if ($line =~ /^include => /){
			
		}elsif ($line =~ /^exten => /){
			$line =~ s/exten => //;
			my @array_ext_did = split (/,/,$line,-1);
			if ($array_ext_did[1] eq 'n(dest-ext)'){
				if ($array_ext_did[2] eq 'Goto(from-did-direct'){
					$hash_did{$array_ext_did[3]}{$array_ext_did[0]} = 1;
				}elsif ($array_ext_did[2] eq 'Goto(ext-group'){
					$hash_group{$array_ext_did[3]}{$array_ext_did[0]} = 1;
#					print "$array_ext_did[3]\t$array_ext_did[0]\n";
				}elsif ($array_ext_did[2] =~ /^Goto\(ivr-\d+/){
					$array_ext_did[2] =~ s/Goto\(//;
					$hash_ivr{$array_ext_did[2]}{$array_ext_did[0]} = 1;
#					print "$array_ext_did[2]\t$array_ext_did[0]\n";
					&ivr($array_ext_did[2]);
				}
			}
		}
	}elsif ($direction eq 'ext-group'){
		if ($line =~ /^include /){
			
		}elsif ($line =~ /^exten /){
			$line =~ s/exten => //;
			my @array_ext_group = split (/,/,$line,-1);
			if ($array_ext_group[1] eq 'n(NORGVQANNOUNCE)'){
				$array_ext_group[5] =~ s/\)//;
				if ($array_ext_group[5] =~ /-/){
					my @array_ext_group_nc = split (/-/,$array_ext_group[5],-1);
					foreach my $number_centrex (@array_ext_group_nc){
						$hash_ext_group{$number_centrex}{$array_ext_group[0]} = 1;
					}
				}else{
					$hash_ext_group{$array_ext_group[5]}{$array_ext_group[0]} = 1;
				}
			}
		}
	}elsif ($direction =~ /^ivr-/){
		if ($line =~ /^include => /){
			
		}elsif ($line =~ /^exten => \d/){
			$line =~ s/exten => //;
			my @array_ivr = split (/,/,$line,-1);
			if ($array_ivr[2] eq 'Goto(ext-group'){
				$hash_ivr_number_group{$array_ivr[3]}{$direction} = $array_ivr[0];
#				print "$array_ivr[3]\t$direction\t$array_ivr[0]\n";
			}
		}
	}
}

sub ivr {
	my $ivr = shift;
	my $ivr_yes = 0;
	open (my $file_ivr, '<:encoding(UTF-8)', "$dir_conf_asterisk/$file_extensions_additional") || die "Error opening file: $file_extensions_additional $!";
		while (defined(my $line_extensions_additional = <$file_ivr>)){
			if ($line_extensions_additional =~ /^\r?$/){
				next;
			}
			if ($line_extensions_additional =~ /^\[$ivr\] /){
#				print "$line_extensions_additional\n";
				$ivr_yes = 1;
				next;
			}elsif ($line_extensions_additional =~ /^\;--== end of \[$ivr\] ==--\;$/){
#				print "$line_extensions_additional\n";
				$ivr_yes = 0;
				last;
			}elsif ($ivr_yes == 1){
				chomp ($line_extensions_additional);
				&parsing ($ivr,$line_extensions_additional);
			}else{
				next;
			}
		}
	close ($file_ivr);
}

sub diff_file{
	my $dir_file = shift;
	my $tmp_dir_file = shift;
	my $original_file = shift;
	
	my $diff_file = `diff -u $dir_file/$original_file $tmp_dir_file/${date_time_file}_${original_file}`;
	if ($diff_file ne ''){
		`diff -u $dir_file/${original_file} $tmp_dir_file/${date_time_file}_${original_file} > /$history_dir/$date_directory/${date_time_file}_${original_file}.diff`;
		`cat $dir_file/${original_file} > /$history_dir/$date_directory/${date_time_file}_${original_file}`;
		`cat $tmp_dir_file/${date_time_file}_${original_file} > $dir_file/$original_file`;
		`cp $dir_file/phonebook_${domen}.xls /mnt/fax/secretary/phonebook/phonebook_${domen}.xls`;
		
		open (my $file_phonebook_diff, '<:encoding(windows-1251)', "/$history_dir/$date_directory/${date_time_file}_${original_file}.diff") || die "Error opening file: ${date_time_file}_${original_file}.diff $!";
			while (defined(my $line_phonebook_diff = <$file_phonebook_diff>)){
				my $new_text = '';
				my $collor = '\#00cc00';
				if ($line_phonebook_diff =~ /^(\-|\+)[А-Яа-яA-Za-z]/){
					chomp($line_phonebook_diff);
					if ($line_phonebook_diff =~ /^\-/){
						$line_phonebook_diff =~ s/\-//;
						$collor = '\#ff6666';
					}else{
						$line_phonebook_diff =~ s/\+//;
						$collor = '\#00cc00'
					}
					$new_text = join ("\<\/td\>\<td\>", split (/\;/,$line_phonebook_diff,-1));
					$new_text = '<td>'."$new_text".'</td>';
				}else{
					next;
				}
#				print "$new_text\n";
				$text = "$text".'<tr style=\"background: '."$collor".'\">'."$new_text".'</tr>';
			}
		close ($file_phonebook_diff);
		$text = "$text".'</table></html>';
#		print "$text\n";
		system("/usr/bin/sendEmail -f phonebook\@$domen -t $user_email_phonebook -u Изменения в телефонном справочнике сотрудников -o message-charset=utf-8 \\
			-m \"$text\" \\
			-s localhost -a $dir_file/phonebook_${domen}.xls");
	}
	`rm $tmp_dir_file/${date_time_file}_${original_file}`;
}
