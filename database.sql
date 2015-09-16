create table shareitem (icon char(255), path char(255), has_keys boolean, is_share boolean, is_shared boolean, modified_at datetime, title char(255), is_dir boolean);
create table shares (id int AUTO_INCREMENT, user char(255), path char(255) );
create table invitations (id int AUTO_INCREMENT, sender char(255), receiver char(255), share_id int, state char(255));



-- this is (sqlite) default/test data, [cs]hould be removed before launch
insert into shareitem VALUES('', 'ponies', 0, 0, 0, DATETIME(), 'ponies', 0);
insert into shareitem VALUES('', 'path', 0, 0, 0, DATETIME(), 'path', 0);
insert into shareitem VALUES('', 'path2', 0, 0, 0, DATETIME(), 'path2', 0);

insert into shares (user, path) VALUES ('user', 'path');
