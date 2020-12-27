drop table if exists topics;
	create table topics (
		id integer primary key autoincrement,
		name text not null,
		description text not null
	);