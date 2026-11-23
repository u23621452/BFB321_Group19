-- StockFlow Engine: MySQL schema (generated from the models by make_schema.py)
-- Usage:  CREATE DATABASE stockflow CHARACTER SET utf8mb4;  USE stockflow;  then run this file.

CREATE TABLE products (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	sku VARCHAR(30) NOT NULL, 
	description VARCHAR(120) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	bin_location VARCHAR(20) NOT NULL, 
	on_hand INTEGER NOT NULL, 
	unit_cost DECIMAL(10, 2) NOT NULL, 
	lead_time_days INTEGER NOT NULL, 
	min_order_qty INTEGER NOT NULL, 
	pack_size INTEGER NOT NULL, 
	daily_demand FLOAT NOT NULL, 
	daily_demand_std FLOAT NOT NULL, 
	annual_demand FLOAT NOT NULL, 
	order_cost DECIMAL(10, 2) NOT NULL, 
	holding_cost DECIMAL(10, 2) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_products_on_hand CHECK (on_hand >= 0)
);
CREATE UNIQUE INDEX ix_products_sku ON products (sku);

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE jobs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	job_number VARCHAR(20) NOT NULL, 
	customer VARCHAR(80) NOT NULL, 
	description VARCHAR(100) NOT NULL, 
	start_date DATE NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (job_number), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE INDEX ix_jobs_status_start ON jobs (status, start_date);

CREATE TABLE material_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	qty INTEGER NOT NULL, 
	note VARCHAR(120), 
	status VARCHAR(10) NOT NULL, 
	requested_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_material_requests_qty CHECK (qty > 0), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id)
);

CREATE TABLE job_lines (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	job_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	qty INTEGER NOT NULL, 
	picked_qty INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_job_product UNIQUE (job_id, product_id), 
	CONSTRAINT ck_job_lines_qty CHECK (qty > 0), 
	CONSTRAINT ck_job_lines_picked CHECK (picked_qty >= 0), 
	FOREIGN KEY(job_id) REFERENCES jobs (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE TABLE stock_movements (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_id INTEGER NOT NULL, 
	job_id INTEGER, 
	user_id INTEGER, 
	qty INTEGER NOT NULL, 
	kind VARCHAR(10) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(job_id) REFERENCES jobs (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_movements_product_time ON stock_movements (product_id, created_at);
