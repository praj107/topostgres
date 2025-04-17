CREATE TABLE discord_user_badges (
  discordid BIGINT NOT NULL,
  id VARCHAR(60) NOT NULL,
  description text NOT NULL,
  icon_id VARCHAR(60) NOT NULL,
  link TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (discordid,icon_id),
  UNIQUE KEY discordid_UNIQUE (discordid,id,description(255),icon_id,link(255)),
  KEY icon_id_index (icon_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

CREATE TABLE discord_user_badges_icons (
  icon_id VARCHAR(60) NOT NULL,
  icon BLOB,
  timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (icon_id),
  UNIQUE KEY id_UNIQUE (icon_id,icon(255)),
  CONSTRAINT icon_id FOREIGN KEY (icon_id) REFERENCES discord_user_badges (icon_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
