CREATE TABLE bios (
    id bigint NOT NULL,
    bio text NOT NULL,
    pros varchar(45) DEFAULT NULL,
    timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (discordid,timestamp),
    UNIQUE KEY UNIQUE (bio(255),pros)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci