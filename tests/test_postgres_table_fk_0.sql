CREATE TABLE discord_user_badges (
    discordid BIGINT NOT NULL,
    id VARCHAR(60) NOT NULL,
    description TEXT NOT NULL,
    icon_id VARCHAR(60) NOT NULL,
    link TEXT NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (discordid, icon_id),
    UNIQUE (discordid, id, description, icon_id, link)
);

CREATE TABLE discord_user_badges_icons (
    icon_id VARCHAR(60) NOT NULL,
    icon BYTEA,
    timestamp TIMESTAMP WITHOUT TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (icon_id),
    UNIQUE (icon_id, icon)
);

