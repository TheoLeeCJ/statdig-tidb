-- Users table (username as primary key)
CREATE TABLE IF NOT EXISTS `users` (
    `username` VARCHAR(50) PRIMARY KEY,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `password_hash` TEXT NOT NULL,
    `role` ENUM('admin', 'user') DEFAULT 'user',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_active` BOOLEAN DEFAULT TRUE
);

-- Sample files table (md5 as primary key)
CREATE TABLE IF NOT EXISTS `samples` (
    `md5` VARCHAR(32) PRIMARY KEY,
    `original_filename` VARCHAR(255) NOT NULL,
    `file_size` BIGINT NOT NULL,
    `filetype` VARCHAR(100),
    `file_description` TEXT,
    `uploaded_by` VARCHAR(50) NOT NULL,
    `analyze_state` INT DEFAULT 0, -- 0: uploaded, 1: extracting, 2: extracted, 3: analysing, 4: analysed
    `is_public` BOOLEAN DEFAULT FALSE,
    `malicious` VARCHAR(24), -- null until analysed
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `overview` TEXT,
    `overview_vec` VECTOR(1024) GENERATED ALWAYS AS (
        EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", `overview`)
    ) STORED,
    FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`username`),
    FULLTEXT INDEX (overview) WITH PARSER STANDARD,
    VECTOR INDEX idx_embedding ((VEC_COSINE_DISTANCE(`overview_vec`)))
);

-- Function extraction table (sample_md5_function_name as primary key)
CREATE TABLE IF NOT EXISTS `functions` (
    `id` VARCHAR(255) PRIMARY KEY,  -- format: sample_md5_function_name
    `sample_md5` VARCHAR(32) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `c_code` TEXT,
    `signature` TEXT,
    `description` TEXT,
    `description_vec` VECTOR(1024) GENERATED ALWAYS AS (
        EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", `description`)
    ) STORED,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`sample_md5`) REFERENCES `samples`(`md5`),
    INDEX `idx_sample_func` (`sample_md5`, `name`),
    FULLTEXT INDEX (description) WITH PARSER STANDARD,
    VECTOR INDEX idx_embedding ((VEC_COSINE_DISTANCE(`description_vec`)))
);

-- Tags table
CREATE TABLE IF NOT EXISTS `tags` (
    `tagId` VARCHAR(8) PRIMARY KEY,
    `tag_content` TEXT NOT NULL
);

-- Tags to samples
CREATE TABLE IF NOT EXISTS `tags_sample` (
    `tagId` VARCHAR(8) NOT NULL,
    `sample_md5` VARCHAR(32) NOT NULL,
    PRIMARY KEY (`tagId`, `sample_md5`),
    FOREIGN KEY (`tagId`) REFERENCES `tags`(`tagId`),
    FOREIGN KEY (`sample_md5`) REFERENCES `samples`(`md5`)
);

-- Tags to functions
CREATE TABLE IF NOT EXISTS `tags_function` (
    `tagId` VARCHAR(8) NOT NULL,
    `function_id` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`tagId`, `function_id`),
    FOREIGN KEY (`tagId`) REFERENCES `tags`(`tagId`),
    FOREIGN KEY (`function_id`) REFERENCES `functions`(`id`)
);

-- Sample details table
CREATE TABLE IF NOT EXISTS `sample_details` (
    `id` VARCHAR(32) PRIMARY KEY, -- same as sample md5
    `full_report` TEXT,
    `full_report_vector` VECTOR(1024) GENERATED ALWAYS AS (
        EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", `full_report`)
    ) STORED,
    `organiser_data` TEXT,
    `responder_data` TEXT,
    FULLTEXT INDEX (full_report) WITH PARSER STANDARD,
    VECTOR INDEX idx_full_report ((VEC_COSINE_DISTANCE(`full_report_vector`)))
);

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO `users` (`username`, `email`, `password_hash`, `role`) VALUES 
('admin', 'admin@example.com', '$argon2id$v=19$m=65536,t=3,p=4$zYYVQ7zLYYK+DBx+7s1A0A$JUiDDs5A0aXIjI3TKjDEryQSWEfMC2k9eHS9KdbUWKo', 'admin');
