
CREATE DATABASE IF NOT EXISTS dbmoc;

USE dbmoc;

CREATE TABLE `upload` (
  `id` int NOT NULL,
  `start_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `load_img` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_processed` tinyint(1) NOT NULL DEFAULT "0",
  `end_date` datetime DEFAULT NULL,
  `class` varchar(255) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `result_imgs` text DEFAULT NULL
);

ALTER TABLE `upload`
    ADD PRIMARY KEY (`id`);

ALTER TABLE `upload`
    MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
COMMIT;