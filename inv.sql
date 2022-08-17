CREATE TABLE `groups` (
  `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `group` text NOT NULL,
  `name` text NOT NULL,
  `type` text NOT NULL
);

CREATE TABLE `vars` (
    `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` text NOT NULL,
    `type` text NOT NULL,
    `key` text NOT NULL,
    `value` text NOT NULL
);
