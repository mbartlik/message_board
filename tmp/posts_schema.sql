drop table if exists posts;
	create table posts (
		id integer primary key autoincrement,
		content text not null,
		created timestamp default CURRENT_TIMESTAMP not null ,
		topic int references topics(id)
	);