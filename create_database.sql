-- ============================================================
-- Tables Created
-- ============================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE SCHEMA IF NOT EXISTS `mydb`;
USE `mydb`;

CREATE TABLE IF NOT EXISTS `member` (
  `member_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NULL,
  `email` VARCHAR(100) NOT NULL,
  `status` ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
  PRIMARY KEY (`member_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `memberships` (
  `membership_id` INT NOT NULL AUTO_INCREMENT,
  `membership_name` ENUM('Bronze', 'Silver', 'Gold', 'Platinum') NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `duration_months` INT NOT NULL,
  PRIMARY KEY (`membership_id`),
  UNIQUE INDEX `membership_name_UNIQUE` (`membership_name` ASC))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `staff` (
  `staff_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `phone_number` VARCHAR(15) NULL,
  `email` VARCHAR(100) NOT NULL,
  `hire_date` DATE NOT NULL,
  `salary` DECIMAL(7,2) NOT NULL,
  `status` ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
  `role` VARCHAR(20) NOT NULL,
  `last_day` DATE NULL DEFAULT NULL,
  PRIMARY KEY (`staff_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC),
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `trainers` (
  `staff_id` INT NOT NULL,
  `certification` VARCHAR(100) NULL,
  PRIMARY KEY (`staff_id`),
  CONSTRAINT `fk_trainers_staff1`
    FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `class_type` (
  `class_type_id` INT NOT NULL AUTO_INCREMENT,
  `class_name` VARCHAR(100) NULL,
  `difficulty_level` VARCHAR(20) NULL,
  PRIMARY KEY (`class_type_id`))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `classes` (
  `class_id` INT NOT NULL AUTO_INCREMENT,
  `scheduled_time` DATETIME NULL,
  `duration_minutes` INT NULL,
  `capacity` INT NULL,
  `trainers_staff_id` INT NOT NULL,
  `class_type_id` INT NOT NULL,
  PRIMARY KEY (`class_id`),
  CONSTRAINT `fk_classes_trainers1`
    FOREIGN KEY (`trainers_staff_id`) REFERENCES `trainers` (`staff_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_classes_class_type1`
    FOREIGN KEY (`class_type_id`) REFERENCES `class_type` (`class_type_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `member_membership` (
  `member_membership_id` INT NOT NULL AUTO_INCREMENT,
  `member_id` INT NOT NULL,
  `membership_id` INT NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NULL,
  PRIMARY KEY (`member_membership_id`),
  CONSTRAINT `fk_member_has_memberships_member1`
    FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_member_has_memberships_memberships1`
    FOREIGN KEY (`membership_id`) REFERENCES `memberships` (`membership_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `class_enrollment` (
  `class_enrollment_id` INT NOT NULL AUTO_INCREMENT,
  `class_id` INT NOT NULL,
  `member_id` INT NOT NULL,
  `signup_date` DATE NULL,
  `attendance_status` ENUM('registered', 'attended', 'missed', 'cancelled') NOT NULL,
  PRIMARY KEY (`class_enrollment_id`),
  UNIQUE INDEX `uq_class_member` (`class_id`, `member_id`),
  CONSTRAINT `fk_classes_has_member_classes1`
    FOREIGN KEY (`class_id`) REFERENCES `classes` (`class_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_classes_has_member_member1`
    FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `payments` (
  `payment_id` INT NOT NULL AUTO_INCREMENT,
  `member_id` INT NOT NULL,
  `amount` DECIMAL(8,2) NOT NULL,
  `payment_date` DATE NULL,
  `payment_method` VARCHAR(50) NOT NULL,
  `status` ENUM('pending', 'completed', 'failed', 'refunded') NULL,
  `payment_type` ENUM('membership', 'class') NOT NULL,
  `member_membership_id` INT NULL,
  `class_enrollment_id` INT NULL,
  PRIMARY KEY (`payment_id`),
  CONSTRAINT `fk_payments_member1`
    FOREIGN KEY (`member_id`) REFERENCES `member` (`member_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_payments_member_membership1`
    FOREIGN KEY (`member_membership_id`) REFERENCES `member_membership` (`member_membership_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_payments_class_enrollment1`
    FOREIGN KEY (`class_enrollment_id`) REFERENCES `class_enrollment` (`class_enrollment_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `chk_payment_ref` CHECK (
    (member_membership_id IS NOT NULL AND class_enrollment_id IS NULL)
    OR
    (member_membership_id IS NULL AND class_enrollment_id IS NOT NULL)
  ))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `equipment` (
  `equipment_id` INT NOT NULL AUTO_INCREMENT,
  `equipment_name` VARCHAR(45) NOT NULL,
  `purchase_date` DATE NOT NULL,
  PRIMARY KEY (`equipment_id`))
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `maintenance` (
  `maintenance_id` INT NOT NULL AUTO_INCREMENT,
  `equipment_id` INT NOT NULL,
  `maintenance_date` DATE NOT NULL,
  `staff_id` INT NOT NULL,
  PRIMARY KEY (`maintenance_id`),
  CONSTRAINT `fk_maintenance_equipment1`
    FOREIGN KEY (`equipment_id`) REFERENCES `equipment` (`equipment_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_maintenance_staff1`
    FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
    ON DELETE NO ACTION ON UPDATE NO ACTION)
ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;


-- ============================================================

-- STEP 2: VIEWS

-- ============================================================

CREATE OR REPLACE VIEW `active_memberships` AS
SELECT
    m.member_id,
    m.name,
    m.email,
    ms.membership_name,
    mm.start_date,
    mm.end_date
FROM member m
JOIN member_membership mm ON m.member_id = mm.member_id
JOIN memberships ms ON mm.membership_id = ms.membership_id
WHERE mm.end_date IS NULL OR mm.end_date >= CURDATE();

-- ----

CREATE OR REPLACE VIEW `class_enrollment_summary` AS
SELECT
    c.class_id,
    ct.class_name,
    c.scheduled_time,
    c.capacity,
    COUNT(ce.member_id) AS enrolled_count,
    (c.capacity - COUNT(ce.member_id)) AS spots_remaining
FROM classes c
JOIN class_type ct ON c.class_type_id = ct.class_type_id
LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
GROUP BY c.class_id, ct.class_name, c.scheduled_time, c.capacity;

-- ----

CREATE OR REPLACE VIEW `member_payment_details` AS
SELECT
    m.name AS member_name,
    p.payment_id,
    p.amount,
    p.payment_date,
    p.payment_type,
    p.status,
    p.member_id,
    ms.membership_name,
    ct.class_name
FROM payments p
JOIN member m ON p.member_id = m.member_id
LEFT JOIN member_membership mm ON p.member_membership_id = mm.member_membership_id
LEFT JOIN memberships ms ON mm.membership_id = ms.membership_id
LEFT JOIN class_enrollment ce ON p.class_enrollment_id = ce.class_enrollment_id
LEFT JOIN classes c ON ce.class_id = c.class_id
LEFT JOIN class_type ct ON c.class_type_id = ct.class_type_id;


-- ============================================================

-- STEP 3: FUNCTIONS

-- ============================================================

CREATE FUNCTION is_member_active(p_member_id INT)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE active_count INT;
    SELECT COUNT(*) INTO active_count
    FROM member_membership
    WHERE member_id = p_member_id
      AND (end_date IS NULL OR end_date >= CURDATE());
    RETURN active_count > 0;
END;

-- ----

CREATE FUNCTION get_total_payments(p_member_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT IFNULL(SUM(amount), 0) INTO total
    FROM payments
    WHERE member_id = p_member_id
      AND status = 'completed';
    RETURN total;
END;

-- ----

CREATE FUNCTION get_available_spots(p_class_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE capacity_val INT;
    DECLARE enrolled INT;
    SELECT capacity INTO capacity_val FROM classes WHERE class_id = p_class_id;
    SELECT COUNT(*) INTO enrolled FROM class_enrollment WHERE class_id = p_class_id;
    RETURN capacity_val - enrolled;
END;


-- ============================================================
-- STEP 4: PROCEDURES
-- ============================================================

CREATE PROCEDURE enroll_member_in_class (
    IN p_member_id INT,
    IN p_class_id INT
)
BEGIN
    DECLARE current_count INT;
    DECLARE max_capacity INT;
    DECLARE already_enrolled INT;

    SELECT COUNT(*) INTO already_enrolled
    FROM class_enrollment
    WHERE member_id = p_member_id AND class_id = p_class_id;

    IF already_enrolled > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Member already enrolled in this class';
    END IF;

    SELECT COUNT(*) INTO current_count
    FROM class_enrollment
    WHERE class_id = p_class_id;

    SELECT capacity INTO max_capacity
    FROM classes
    WHERE class_id = p_class_id;

    IF current_count >= max_capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Class is full';
    ELSE
        INSERT INTO class_enrollment (class_id, member_id, signup_date, attendance_status)
        VALUES (p_class_id, p_member_id, CURDATE(), 'registered');
    END IF;
END;

-- ----

CREATE PROCEDURE add_membership_payment (
    IN p_member_id INT,
    IN p_membership_id INT,
    IN p_amount DECIMAL(8,2)
)
BEGIN
    DECLARE mm_id INT;

    SELECT member_membership_id INTO mm_id
    FROM member_membership
    WHERE member_id = p_member_id
      AND membership_id = p_membership_id
      AND (end_date IS NULL OR end_date >= CURDATE())
    LIMIT 1;

    IF mm_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No active membership found';
    ELSE
        INSERT INTO payments (
            member_id, amount, payment_date, payment_method,
            status, payment_type, member_membership_id
        )
        VALUES (
            p_member_id, p_amount, CURDATE(), 'card',
            'completed', 'membership', mm_id
        );
    END IF;
END;


-- ============================================================

-- STEP 5: TRIGGERS

-- ============================================================

CREATE TRIGGER prevent_class_overbooking
BEFORE INSERT ON class_enrollment
FOR EACH ROW
BEGIN
    DECLARE current_count INT;
    DECLARE max_capacity INT;

    SELECT COUNT(*) INTO current_count
    FROM class_enrollment
    WHERE class_id = NEW.class_id;

    SELECT capacity INTO max_capacity
    FROM classes
    WHERE class_id = NEW.class_id;

    IF current_count >= max_capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot enroll: class is full';
    END IF;
END;

-- ----

CREATE TRIGGER set_membership_end_date
BEFORE INSERT ON member_membership
FOR EACH ROW
BEGIN
    DECLARE duration INT;
    SELECT duration_months INTO duration
    FROM memberships
    WHERE membership_id = NEW.membership_id;
    SET NEW.end_date = DATE_ADD(NEW.start_date, INTERVAL duration MONTH);
END;

-- ----

CREATE TRIGGER set_payment_status
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
    IF NEW.status IS NULL THEN
        SET NEW.status = 'completed';
    END IF;
END;

-- ----

CREATE TRIGGER validate_payment_reference
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
    IF (NEW.member_membership_id IS NULL AND NEW.class_enrollment_id IS NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Payment must reference either a membership or a class';
    END IF;

    IF (NEW.member_membership_id IS NOT NULL AND NEW.class_enrollment_id IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Payment cannot reference both membership and class';
    END IF;
END;

-- ----

CREATE TRIGGER prevent_multiple_active_memberships
BEFORE INSERT ON member_membership
FOR EACH ROW
BEGIN
    DECLARE active_count INT;

    SELECT COUNT(*) INTO active_count
    FROM member_membership
    WHERE member_id = NEW.member_id
      AND (end_date IS NULL OR end_date >= CURDATE());

    IF active_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Member already has an active membership';
    END IF;
END;