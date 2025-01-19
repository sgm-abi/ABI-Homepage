<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the web site, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://wordpress.org/documentation/article/editing-wp-config-php/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'dbs12700874' );

/** Database username */
define( 'DB_USER', 'dbu2268703' );

/** Database password */
define( 'DB_PASSWORD', 'gobTos-vyxgap-wosti0!?' );

/** Database hostname */
define( 'DB_HOST', 'db5015549151.hosting-data.io' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',         '?>3P9~wz2OU|Tk%#]%B~gW@Zrf4(XrA+jw71#3$-(}Zbcw9.~c9-PEwnm!}{n F?' );
define( 'SECURE_AUTH_KEY',  '[ksS$>1-8S7;R^0.;9ocwX-Co:?Ju)~--BqHpgUVc%i|;?&bMJx})SW?=(u{/cq.' );
define( 'LOGGED_IN_KEY',    'h7oSxXnIAi1ao)jzzhobW>Qm HTJqQ}QQB:T&Q|)o]jx&l4&rZ=>xXn30NStL1!!' );
define( 'NONCE_KEY',        'Xt`O?Wx*[j8~KC)`UnJ!W`&bJ9n[*d@R5hF.p7!i2WlJ}*F2WN@zE7Ox.vG&/hSB' );
define( 'AUTH_SALT',        'E?)fG[>`2X:cI]-H(c`L`sbipsB}]5PQ).0>kBeH&0w-y(`3!IR2[Q<szdYDpIT-' );
define( 'SECURE_AUTH_SALT', ':zUajobfot^#}?gTlL_ViDk30!y(wvQfu_r0aql3S4O;?Pjsm^Y?O>On!9+0lKJ~' );
define( 'LOGGED_IN_SALT',   ':%36{W`.JqEZ]A !|g^|-r/EBZj;%%Qc[[m,A]5Jrk6W,f$;QlCj!Qq^<oA3=6~L' );
define( 'NONCE_SALT',       'R9!}ro8Zp(38B**BUViX7ofu,fX>e.a_(/NF-HZut)l*xYu49-G]tW7bE(w#EqNW' );

/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://wordpress.org/documentation/article/debugging-in-wordpress/
 */
define( 'WP_DEBUG', false );

/* Add any custom values between this line and the "stop editing" line. */



/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
