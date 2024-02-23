#include <LiveXTorchPlugin.h>
#include "version.h"
#include <boost/algorithm/string.hpp>

using namespace OdinData;

namespace FrameProcessor
{

  const std::string LiveXTorchPlugin::CONFIG_MODEL_PATH = "model_path";
  const std::string LiveXTorchPlugin::CONFIG_PREPROCESSOR_PATH = "preprocessor_path";
  const std::string LiveXTorchPlugin::CONFIG_DECODE_HEADER = "decode_header";
    /*
    * The Constructor
    */
  LiveXTorchPlugin::LiveXTorchPlugin()
  {
    logger_ = Logger::getLogger("FP.LiveXTorchPlugin");
    LOG4CXX_INFO(logger_, "LiveX ML Plugin Version" << this->get_version_long() << " Loaded.");

  }

  LiveXTorchPlugin::~LiveXTorchPlugin()
  {
    LOG4CXX_TRACE(logger_, "LiveX ML Plugin Destructor");
  }

  void LiveXTorchPlugin::configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply)
  {
      //load the model?
      if(config.has_param(LiveXTorchPlugin::CONFIG_MODEL_PATH))
      {
        
        model_path = config.get_param<std::string>(LiveXTorchPlugin::CONFIG_MODEL_PATH);
        LOG4CXX_INFO(logger_, "LiveX ML Plugin Loading Model: " << model_path);
        loadModel(model_path, torch::cuda::is_available());
      }
      if(config.has_param(LiveXTorchPlugin::CONFIG_PREPROCESSOR_PATH))
      {
        preprocessor_path = config.get_param<std::string>(LiveXTorchPlugin::CONFIG_PREPROCESSOR_PATH);
        LOG4CXX_INFO(logger_, "LiveX Torch Plugin Loading Preprocessor Model: "<< preprocessor_path);
        preprocessor = torch::jit::load(preprocessor_path);
        preprocessor.eval();

        preprocessor_loaded = true;
      }
      if(config.has_param(LiveXTorchPlugin::CONFIG_DECODE_HEADER))
      {
        decode_header = config.get_param<bool>(LiveXTorchPlugin::CONFIG_DECODE_HEADER);
      }

      // if(config.has_param(LiveXTorchPlugin::CONFIG_DIMENSIONS))
      // {
      //   // LOG4CXX_INFO(logger_, )
      //   frame_dimensions = config.get_param<std::vector<long int>>(LiveXTorchPlugin::CONFIG_DIMENSIONS);
      // }
  }

  void LiveXTorchPlugin::requestConfiguration(OdinData::IpcMessage& reply)
  {
      std::string base_str = get_name() + "/";
      reply.set_param(base_str + LiveXTorchPlugin::CONFIG_MODEL_PATH, model_path);
  }

  void LiveXTorchPlugin::status(OdinData::IpcMessage& status)
  {
      LOG4CXX_DEBUG(logger_, "Status Requested for LiveXTorchPlugin");
      std::string base_str = get_name() + "/";
      status.set_param(base_str + "model_loaded", model_loaded);
      status.set_param(base_str + "preprocessor_loaded", preprocessor_loaded);
      status.set_param(base_str + "decode_header", decode_header);

  }

  void LiveXTorchPlugin::loadModel(std::string path, bool gpu_avail)
  {
    c10::Device device = c10::Device(torch::kCPU);
    if(gpu_avail)
    {
      device = c10::Device(torch::kCUDA, 1);
    }
    try{
      model = torch::jit::load(path, device);

      LOG4CXX_DEBUG(logger_, "Model Loaded on device: " << device.type());
    }
    catch (const std::runtime_error& error)
    {

    }
  }

  void LiveXTorchPlugin::decodeHeader(boost::shared_ptr<Frame> frame)
  {
      LOG4CXX_DEBUG(logger_, "Decoding Frame Header");
      LiveX::FrameHeader* hdr_ptr = static_cast<LiveX::FrameHeader*>(frame->get_data_ptr());

      FrameMetaData metadata;

      metadata.set_dataset_name("LiveX");
      metadata.set_data_type((DataType)hdr_ptr->frame_data_type);
      metadata.set_frame_number(hdr_ptr->frame_number);
      metadata.set_compression_type(no_compression);
      dimensions_t dims(2);
      dims[1] = hdr_ptr->frame_height;
      dims[0] = hdr_ptr->frame_width;
      metadata.set_dimensions(dims);

      frame->set_meta_data(metadata);
      frame->set_image_offset(sizeof(LiveX::FrameHeader));
      frame->set_image_size(hdr_ptr->frame_height*hdr_ptr->frame_width * sizeof(uint8_t));
  }

  void LiveXTorchPlugin::process_frame(boost::shared_ptr<Frame> frame)
  {
    if(decode_header){
      decodeHeader(frame);
    }
    if(model_loaded)
      {

      const void* frame_data = frame->get_image_ptr();
      const FrameMetaData meta_data = frame->get_meta_data();
      dimensions_t dims = meta_data.get_dimensions();

      std::vector<long int> input_dims = std::vector<long int>(dims.begin(), dims.end());

      torch::Tensor input = torch::from_blob((void*)frame_data, input_dims, torch::kByte);

      input = input.toType(torch::kFloat32).div(255.0);  //starts as a byte, we want it to be float for the current model
      
      // input = torch::data::transforms::Normalize<>((0.5), (0.5))(input);
      if(preprocessor_loaded)
      {
        LOG4CXX_DEBUG(logger_, "Preprocessing Input");
        input = preprocessor.forward({input}).toTensor();
      }

      //TEMP UNSQUEZES TO GET THE IMAGE TO FIT IN CURRENT MODEL
      input = input.unsqueeze(0);
      input = input.unsqueeze(0);

      std::vector<torch::jit::IValue> input_vector;
      input_vector.push_back(input);

      try {
      torch::Tensor output = model.forward(input_vector).toTensor();
      LOG4CXX_DEBUG(logger_, "Result: " << output);
      frame->meta_data().set_dataset_name("Test");
      //turn frame into Tensor
      //run through loaded model
      //output original frame and result from model
      }
      catch (const std::runtime_error& error)
      {
        LOG4CXX_ERROR(logger_, "Runtime Error running mode: " << error.what());
      }
    }

    LOG4CXX_DEBUG(logger_, "Pushing Data Frame" );
    this->push(frame);

    // make results frame
    boost::shared_ptr<Frame> results_frame;




  }

  bool LiveXTorchPlugin::reset_statistics()
  {
    //empty method for now?
    return true;
  }

  int LiveXTorchPlugin::get_version_major()
  {
    return ODIN_DATA_VERSION_MAJOR;
  }
  int LiveXTorchPlugin::get_version_minor()
  {
    return ODIN_DATA_VERSION_MINOR;
  }
  int LiveXTorchPlugin::get_version_patch()
  {
    return ODIN_DATA_VERSION_PATCH;
  }
  std::string LiveXTorchPlugin::get_version_short()
  {
    return ODIN_DATA_VERSION_STR_SHORT;
  }
  std::string LiveXTorchPlugin::get_version_long()
  {
    return ODIN_DATA_VERSION_STR;
  }


}