
class AIGSnapshot:

  def __init__(self, prodmode):
    '''
      :param prodmode: 1 or 0, 1 implies data will be stored in production and 0 implies data will be stored in staging table 
    '''
    self.aigdm_url = aigdm_url
    self.q_cri = q_cri
    self.temp = temp
    self.q_cri = "select * from aigdm.aig_edsr_master_data_0 where typeso = 'BACKLOG'"
    self.default_op_path = 's3://tfsdl-lslpg-fdt-test/'
    self.aig_col_mapping_file_path = f"{self.default_op_path}AIG_Bcklog_Col_Dat_Types.csv"
    self.stage_table_name = "aig_backlogarchive_temp"
    self.prod_table_name = "aig_backlog_snapshot"
    self.prodmode = prodmode

  def get_aig_backlog_data(self):

    spark_df = spark.read.format("com.databricks.spark.redshift") \
        .option("url", self.aigdm_url) \
        .option("query", self.q_cri) \
        .option("tempdir", self.temp) \
        .option("forward_spark_s3_credentials", True) \
        .load()

    return spark_df

  def mod_dat_typ_aigdat(self, df_aig):
    '''
      :param df_aig: Spark data frame input which has AIG Backlog data
    '''
    aig_col_datTyps = spark.read.csv(self.aig_col_mapping_file_path, header=True)
    aig_col_datTyps_dict = dict(aig_col_datTyps.rdd.map(lambda x: (x.col_name, x.dattyp)).collect())
    
    df_aig = df_aig.withColumn('archivedate', F.lit(date.today()))

    col_list = aig_col_datTyps.select('col_name').distinct().rdd.flatMap(lambda x: x).collect()

    df_aig = df_aig.select(*col_list)

    for col in df_aig.columns:
        col_dat_typ = aig_col_datTyps_dict[col]

        if "object" in col_dat_typ:
            df_aig = df_aig.withColumn(col, F.col(col).cast("string"))
        if "int" in col_dat_typ:
            df_aig = df_aig.withColumn(col, F.col(col).cast("int"))
        if "float" in col_dat_typ:
            df_aig = df_aig.withColumn(col, F.col(col).cast("float"))
        if "date" in col_dat_typ:
            df_aig = df_aig.withColumn(col, F.to_date(F.col(col)))

    df_aig = df_aig.withColumn('archivedate', F.to_date(F.col('archivedate')))
    
    return df_aig

  def save_spark_to_hive(self, 
                         in_df, 
                         table_name= "Thermo_Test",
                         append = False,
                         in_path = ''):
    '''
      :param in_df: Spark data frame for final export
      :param table_name: Output table name
      :param append: True or False, True implies the data will append to the table name specified above whereas False will implies the table name will be overwritten
      :param in_path: a default output s3 folder has been specified
    '''
    mode = 'overwrite'
    if (append == True):
      mode = 'append'
    
    if in_path == '':
        in_path = self.default_op_path
    
    tablepath = in_path +table_name
    in_df\
    .write\
    .option("overwriteSchema", "true")\
    .format("delta")\
    .mode(mode)\
    .save(tablepath)

    spark_query= '''create table if not exists tfsdl_lslpg_fdt_test.'''  + table_name  
    spark.sql(spark_query +  ''' using delta  location "''' + tablepath + '''"''' )

    return(spark\
          .read\
          .format("delta")\
          .load(tablepath)\
          .toPandas()\
          .reset_index(drop=True))

  def append_bcklogdat(self):
    print(f"Extracting AIG Backlog data...\n")
    df_aig_latest = self.get_aig_backlog_data()
    print(df_aig_latest.dtypes)
    
    print(f"Formatting/Filtering AIG Backlog data...\n")
    df_aig_latest_ = self.mod_dat_typ_aigdat(df_aig=df_aig_latest)
    print(df_aig_latest_.dtypes)
    print(df_aig_latest_.count())
    
    print(f"Selecting table name based on prod mode...\n")
    table_name = self.stage_table_name
    if self.prodmode == 1:
        table_name = self.prod_table_name
    
    print(f"Saving to Hive in table: {table_name}\n")
    self.save_spark_to_hive(in_df=df_aig_latest_,
                  table_name= table_name,
                  append = True,
                  in_path ='s3://tfsdl-lslpg-fdt-test/')
    print(f"Successfully saved to Hive in table: {table_name}") 